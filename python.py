from argparse import ArgumentParser
from tokenize import generate_tokens
import token
import tokenize
from keyword import iskeyword
from io import StringIO

from derp import parse, Token, ter, Recurrence, BaseParser, one_plus
from derp.utilities import unpack_n
import ast


def generate_parser_tokens(filename):
    with open(filename) as f:
        string_io = StringIO(f.read() + '\n')

    for tok_info in generate_tokens(string_io.readline):

        if tok_info.type == token.NAME:
            value = tok_info.string
            if iskeyword(value):
                yield Token(value, value)

            else:
                yield Token('ID', tok_info.string)

        elif tok_info.type == token.STRING:
            yield Token('LIT', eval(tok_info.string))

        elif tok_info.type == token.NUMBER:
            yield Token('NUMBER', tok_info.string)

        elif tok_info.type in {token.NEWLINE}:
            yield Token("NEWLINE", "NEWLINE")

        elif tok_info.type == token.INDENT:
            yield Token("INDENT", "INDENT")

        elif tok_info.type == token.DEDENT:
            yield Token("DEDENT", "DEDENT")

        elif tok_info.type == token.ERRORTOKEN:
            yield Token("ERROR", tok_info.string)

        elif tok_info.type == token.ENDMARKER:
            yield Token("ENDMARKER", "ENDMARKER")

        elif tok_info.type == tokenize.COMMENT:
            continue

        elif tok_info.type == tokenize.NL:
            continue

        else:
            yield Token(tok_info.string, tok_info.string)


class GrammarFactory:

    def __init__(self):
        object.__setattr__(self, '_recurrences', {})

    def ensure_parsers_defined(self):
        for name, parser in self._recurrences.items():
            if parser.parser is None:
                raise ValueError("{} parser is not defined".format(name))

    def __getattr__(self, name):
        self._recurrences[name] = recurrence = Recurrence()
        object.__setattr__(self, name, recurrence)  # To stop this being created again
        return recurrence

    def __setattr__(self, name, value):
        assert isinstance(value, BaseParser), (name, value)

        # Existing parser is either recurrence or non recurrence
        if hasattr(self, name):
            if name in self._recurrences:
                recurrence = getattr(self, name)
                if recurrence.parser is not None:
                    raise ValueError('Recurrent parser already defined')

                recurrence.parser = value
                recurrence.simple_name = name

            else:
                raise ValueError('Parser already assigned')

        # No recurrence relation (as assignment BEFORE get)
        else:
            object.__setattr__(self, name, value)


def emit_func_def(args):
    _, name, params, ret_type, _, body = unpack_n(args, 6)
    decorators = ()
    if ret_type == '':
        returns = None
    else:
        _, returns = ret_type

    return ast.FunctionDef(name, params, body, decorators, returns)

def emit_params(args):
    _, typed_args, _ = unpack_n(args, 3)
    return typed_args

def emit_del(args):
    return ast.Del()

def emit_break(args):
    return ast.Break()

def emit_pass(args):
    return ast.Pass()

def emit_continue(args):
    return ast.Continue()

def emit_import_from(args):
    pass

def emit_import(args):
    _, names = args
    return ast.Import(names)

def emit_nonlocal(args):
    _, name, names = unpack_n(args, 3)
    if names != '':
        other_names = tuple(n[1] for n in names)
    else:
        other_names = ()
    return ast.Nonlocal((name,) + other_names)

def emit_global(args):
    _, name, names = unpack_n(args, 3)
    if names != '':
        other_names = tuple(n[1] for n in names)
    else:
        other_names = ()
    return ast.Global((name,) + other_names)

def emit_assert(args):
    _, test, msg = unpack_n(args, 3)
    if msg != '':
        _, message = msg
    else:
        message = None
    return ast.Assert(test, message)

def emit_lambda_def(args):
    _, varargs, _, test = unpack_n(args, 4)
    return ast.LambdaDef(varargs, test)

def emit_return(args):
    _, test_list = args
    return ast.Return(test_list)

def emit_if(args):
    _, condition, _, body, elifs, else_ = unpack_n(args, 6)

    if elifs != '':
        other_ifs = tuple([ast.If(else_condition, else_body) for _, else_condition, _, else_body in elifs])
    else:
        other_ifs = ()

    if else_ != '':
        _, _, else_stmt = else_
        other_ifs = other_ifs + (else_stmt,)

    return ast.If(condition, body, other_ifs)

def emit_while(args):
    _, condition, _, body, else_ = unpack_n(args, 5)
    if else_ == '':
        else_stmt = None
    else:
        else_stmt = else_
    return ast.While(condition, body, else_stmt)

def emit_for(args):
    _, target, _, iterable, _, body, optelse = unpack_n(args, 7)
    else_ = None if optelse == '' else optelse
    return ast.If(target, iterable, body, else_)

def emit_with(args):
    _, with_item, with_items, _, body = unpack_n(args, 5)
    if with_items == '':
        all_items = with_item,
    else:
        all_items = (with_item,) + with_items
    return ast.With(all_items, body)

g = GrammarFactory()

g.single_input = (ter('NEWLINE') | g.simple_stmt | g.compound_stmt) & ter('NEWLINE')
# g.eval_input = g.test_list & +ter('NEWLINE') & ter('ENDMARKER')
g.file_input = +(ter('NEWLINE') | g.stmt) & ter('ENDMARKER')

g.decorator = ter('@') & g.dotted_name & ~(ter('(') & ~g.arg_list & ter(')')) & ter('NEWLINE')
g.decorators = one_plus(g.decorator)
g.decorated = g.decorators & (g.class_def | g.func_def)  # Ignore async

g.func_def = (ter('def') & ter('ID') & g.parameters & ~(ter('->') & g.test) & ter(':') & g.suite) >> emit_func_def


def generate_args_list(tfpdef):
    tfpdef_opt_ass = tfpdef & ~(ter('=') & g.test)
    tfpdef_kwargs = ter('**') & tfpdef
    return (tfpdef_opt_ass & +(ter(',') & tfpdef_opt_ass) &
            ~(ter(',') & ~(ter('*') & ~tfpdef & +(ter(',') & tfpdef_opt_ass) & ~( ter(',') & tfpdef_kwargs) | tfpdef_kwargs)) |
            (ter('*') & ~tfpdef & +(ter(',') & tfpdef_opt_ass) & ~(ter(',') & tfpdef_kwargs)) | tfpdef_kwargs)

g.parameters = (ter('(') & g.typed_args_list & ter(')')) >> emit_params

g.typed_args_list = generate_args_list(g.tfpdef)
g.tfpdef = ter('ID') & ~(ter(':') & g.test)

g.var_args_list = generate_args_list(g.vfpdef)
g.vfpdef = ter('ID')

g.stmt = g.simple_stmt | g.compound_stmt
g.simple_stmt = g.small_stmt & +(ter(';') & g.small_stmt) & ~ter(';') & ter('NEWLINE')
g.small_stmt = (g.expr_stmt | g.del_stmt | g.pass_stmt | g.flow_stmt | g.import_stmt | g.global_stmt | g.nonlocal_stmt | g.assert_stmt)
g.expr_stmt = g.test_list_star_expr & (g.augassign & (g.yield_expr | g.test_list) | +(ter('=') & (g.yield_expr | g.test_list_star_expr)))
g.test_list_star_expr = (g.test | g.star_expr) & +(ter(',') & (g.test | g.star_expr)) & ~ter(',')
g.augassign = ter('+=') | ter('-=') | ter('*=') | ter('/=') | ter('%=') | ter('&=') | ter('|=') | ter('^=') | ter('^=') \
              | ter('<<=') | ter('>>=') | ter('**=') | ter('//=') | ter('@=')
g.del_stmt = ter('del') & g.expr_list >> emit_del
g.pass_stmt = ter('pass') >> emit_pass
g.flow_stmt = g.break_stmt | g.continue_stmt | g.return_stmt | g.raise_stmt | g.yield_stmt
g.break_stmt = ter('break') >> emit_break
g.continue_stmt = ter('continue') >> emit_continue
g.return_stmt = (ter('return') & ~g.test_list) >> emit_return
g.yield_stmt = g.yield_expr
g.raise_stmt = ter('raise') & ~(g.test & ~(ter('from') & g.test))
g.import_stmt = g.import_name | g.import_from
g.import_name = (ter('import') & g.dotted_as_names) >> emit_import
g.import_from = (ter('from') & ((+(ter('.') | ter('...')) & g.dotted_name) | one_plus(ter('.') | ter('...'))) & ter('import') & (ter('*') | (ter('(') & g.import_as_names & ter(')')) | g.import_as_names)) >> emit_import_from
g.import_as_name = ter('ID') & ~(ter('as') & ter('ID'))
g.import_as_names = g.import_as_name & +(ter(',') & g.import_as_name) & ~ter(',')
g.dotted_name = ter('ID') & +(ter('.') & ter('ID'))
g.dotted_as_name = g.dotted_name & ~(ter('as') & ter('ID'))
g.dotted_as_names = g.dotted_as_name & +(ter(',') & g.dotted_as_name)
g.global_stmt = (ter('global') & ter('ID') & +(ter(',') & ter('ID'))) >> emit_global
g.nonlocal_stmt = (ter('nonlocal') & ter('ID') & +(ter(',') & ter('ID'))) >> emit_nonlocal
g.assert_stmt = (ter('assert') & g.test & ~(ter(',') & g.test)) >> emit_assert

g.compound_stmt = g.if_stmt | g.while_stmt | g.for_stmt | g.try_stmt | g.with_stmt | g.func_def | g.class_def | g.decorated
g.if_stmt = (ter('if') & g.test & ter(':') & g.suite & +(ter('elif') & g.test & ter(':') & g.suite) & ~(ter('else') & ter(':') & g.suite)) >> emit_if
g.while_stmt = (ter('while') & g.test & ter(':') & g.suite & ~(ter('else') & ter(':') & g.suite)) >> emit_while
g.for_stmt = (ter('for') & g.expr_list & ter('in') & g.test_list & ter(':') & g.suite & ~(ter('else') & ter(':') & g.suite)) >> emit_for
g.try_stmt = ter('try') & ter(':') & g.suite & \
             ((one_plus(g.except_clause & ter(':') & g.suite) &
               ~(ter('else') & ter(':') & g.suite) &
               ~(ter('finally') & ter(':') & g.suite)) |
              # Just finally no except
              (ter('finally') & ter(':') & g.suite)
              )

g.with_stmt = (ter('with') & g.with_item & +(ter(',') & g.with_item) & ter(':') & g.suite) >> emit_with
g.with_item = g.test & ~(ter('as') & g.expr)
g.except_clause = ter('except') & ~(g.test & ~(ter('as') & ter('ID')))
g.suite = g.simple_stmt | (ter('NEWLINE') & ter('INDENT') & one_plus(g.stmt) & ter('DEDENT'))

g.test = (g.or_test & ~(ter('if') & g.or_test & ter('else') & g.test)) | g.lambda_def
g.test_no_cond = g.or_test | g.lambda_def_no_cond

g.lambda_def = (ter('lambda') & ~g.var_args_list & ter(':') & g.test) >> emit_lambda_def
g.lambda_def_no_cond = ter('lambda') & ~g.var_args_list & ter(':') & g.test_no_cond
g.or_test = g.and_test & +(ter('or') & g.and_test)
g.and_test = g.not_test & +(ter('and') & g.not_test)
g.not_test = (ter('not') & g.not_test) | g.comparison
g.comparison = g.expr & +(g.comp_op & g.expr)

g.comp_op = ter('<') | ter('>') | ter('==') | ter('>=') | ter('<=') | ter('<>') | ter('!=') | ter('in') | ter(
    'not') & ter('in') | ter('is') | ter('is') & ter('not')
g.star_expr = ter('*') & g.expr
g.expr = g.xor_expr & +(ter('|') & g.xor_expr)
g.xor_expr = g.and_expr & +(ter('^') & g.and_expr)
g.and_expr = g.shift_expr & +(ter('&') & g.shift_expr)
g.shift_expr = g.arith_expr & +((ter('<<') | ter('>>')) & g.arith_expr)
g.arith_expr = g.term & +((ter('+') | ter('-')) & g.term)
g.term = g.factor & +((ter('*') | ter('@') | ter('/') | ter('%') | ter('//')) & g.factor)
g.factor = ((ter('+') | ter('-') | ter('~')) & g.factor) | g.power
g.power = g.atom_expr & ~(ter('**') & g.factor)
g.atom_expr = g.atom & +g.trailer
g.atom = ((ter('(') & ~(g.yield_expr | g.test_list_comp) & ter(')')) |
          (ter('[') & ~(g.yield_expr | g.test_list_comp) & ter(']')) |
          (ter('{') & ~g.dict_or_set_maker & ter('}')) |
          ter('ID') | ter('NUMBER') | one_plus(ter('LIT')) | ter('...') | ter('None') | ter('True') | ter('False'))
g.test_list_comp = (g.test | g.star_expr) & (g.comp_for | +(ter(',') & (g.test | g.star_expr)) & ~ter(','))
g.trailer = (ter('(') & ~g.arg_list & ter(')')) | (ter('[') & g.subscript_list & ter(']')) | (ter('.') & ter('ID'))
g.subscript_list = g.subscript & +(ter(',') & g.subscript) & ~ter(',')
g.subscript = g.test | (~g.test & ter(':') & ~g.test & ~g.slice_op)
g.slice_op = ter(':') & ~g.test
g.expr_list = (g.expr | g.star_expr) & +(ter(',') & (g.expr | g.star_expr)) & ~ter(',')
g.test_list = g.test & +(ter(',') & g.test) & ~ter(',')
g.dict_or_set_maker = (((g.test & ter(':') & g.test) | (ter('**') & g.expr) &
                        (
                        g.comp_for | +(ter(',') & ((g.test & ter(':') & g.test) | (ter('**') & g.expr))) & ~ter(','))) |
                       ((g.test | g.star_expr) & (g.comp_for | +(ter(',') & (g.test | g.star_expr)) & ~ter(','))))
g.class_def = ter('class') & ter('ID') & ~(ter('(') & ~g.arg_list & ter(')')) & ter(':') & g.suite
g.arg_list = g.argument & +(ter(',') & g.argument) & ~ter(',')

g.argument = ((g.test & ~g.comp_for) |
              (g.test & ter('=') & g.test) |
              (ter('**') & g.test) |
              (ter('*') & g.test))
g.comp_iter = g.comp_for | g.comp_if
g.comp_for = ter('for') & g.expr_list & ter('in') & g.or_test & ~g.comp_iter
g.comp_if = ter('if') & g.test_no_cond & ~g.comp_iter

g.yield_expr = ter('yield') & ~g.yield_arg
g.yield_arg = (ter('from') & g.test) | g.test_list

# Check all parsers were defined
g.ensure_parsers_defined()

if __name__ == "__main__":
    parser = ArgumentParser(description='Python parser')
    parser.add_argument('-filepath', default="sample.py")
    args = parser.parse_args()

    tokens = list(generate_parser_tokens(args.filepath))
    print("Parsing: {} with {} tokens".format(args.filepath, len(tokens)))

    result = parse(g.file_input, tokens)

    if not result:
        print("Failed to parse!")
    else:
        print(result)
