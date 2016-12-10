from argparse import ArgumentParser
from tokenize import generate_tokens
import token
import tokenize
from keyword import iskeyword
from io import StringIO

from derp import parse, Token, ter, Recurrence, BaseParser, one_plus
from derp.utilities import unpack_n
import ast


# TODO support bytes vs string


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

    if params == '':
        params = ()

    return ast.FunctionDef(name, params, body, decorators, returns)

def emit_params(args):
    _, typed_args, _ = unpack_n(args, 3)
    return typed_args

def emit_del(args):
    _, exprs = args
    return ast.Delete(exprs)

def emit_break(args):
    return ast.Break()

def emit_pass(args):
    return ast.Pass()

def emit_continue(args):
    return ast.Continue()

def emit_import_as_name(args):
    id_, opt = args
    if opt == '':
        alias = None
    else:
        _, alias = opt
    return ast.Alias(id_, alias)

def emit_import_from_dotted_name(args):
    many_dots, dotted_name = args
    level = sum(map(len, many_dots))

    first_name, remainder = dotted_name
    module = first_name + ''.join(s for p in remainder for s in p)
    return ast.ImportFromModule(level, module)

def emit_import_from_no_name(args):
    dot_or_dots = args
    level = sum(map(len, dot_or_dots))
    return ast.ImportFromModule(level, None)

def emit_import_from_all(args):
    asterisk, = args
    return ast.Alias(asterisk)

def emit_import_from_names(args):
    alias, remainder, _ = unpack_n(args, 3)

    if remainder == '':
        aliases = alias,
    else:
        commas, following_aliases = zip(*remainder)
        aliases = alias, + following_aliases

    return ast.ImportFromSubModules(aliases)

def emit_import_from_names_paren(args):
    parent, name_args, paren = unpack_n(args, 3)
    return emit_import_from_names(name_args)

def emit_import_from(args):
    _, module, _, submodule = unpack_n(args, 4)
    return ast.ImportFrom(module.module, submodule.aliases, module.level)

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
    return ast.For(target, iterable, body, else_)

def emit_with(args):
    _, with_item, with_items, _, body = unpack_n(args, 5)
    if with_items == '':
        all_items = with_item,
    else:
        all_items = (with_item,) + with_items
    return ast.With(all_items, body)

def emit_try(args):
    _, _, body, following = unpack_n(args, 4)
    raise NotImplemented

def emit_raise(args):
    _, opt_exc = args
    if opt_exc == '':
        return ast.Raise(None, None)

    exc, opt_cause = opt_exc
    if opt_cause == '':
        return ast.Raise(exc, None)
    return ast.Raise(exc, opt_cause)

def emit_kwargs_only(kwarg):
    return ast.Arguments((), None, (), (), kwarg, ())

def emit_tfpdef(args):
    arg_id, opt_annotation = args
    if opt_annotation != '':
        _, annotation = opt_annotation

    else:
        annotation = None

    return ast.Arg(arg_id, annotation)

def emit_varargs(args):
    _, vararg, any_opt_ass, kwarg = unpack_n(args, 4)
    if vararg == '':
        vararg = None

    if kwarg == '':
        kwarg = None

    if any_opt_ass == '':
        opt_ass = ()
    else:
        opt_ass = tuple(v for c, v in any_opt_ass)

    kw_only = []
    kw_defaults = []
    for v in opt_ass:
        arg, ass = v
        if ass != '':
            _, value = ass

        else:
            value = None

        kw_only.append(arg)
        kw_defaults.append(value)

    return ast.Arguments((), vararg, tuple(kw_only), tuple(kw_defaults), kwarg, ())

def emit_first(args):
    opt_ass_first, remaining_opt_ass, opt_remainder = unpack_n(args, 3)

    if remaining_opt_ass == '':
        args_optional_values = (opt_ass_first,)

    else:
        _, following_assignments = zip(*remaining_opt_ass)
        args_optional_values = (opt_ass_first,) + following_assignments

    defaults = []
    args = []

    for arg, ass in args_optional_values:
        if ass != '':
            _, value = ass
            defaults.append(value)

        else:

            if defaults:
                raise SyntaxError("Non-default arg after default arg")

        args.append(arg)

    kwonlyargs = ()
    kw_defaults = ()

    kwarg = None
    vararg = None

    if opt_remainder != '':
        _, remainder = opt_remainder
        if remainder != '':
            first = remainder[0]

            if first == '**':
                _, kwarg = remainder

            else:
                args_varargs = emit_varargs(remainder)

                vararg = args_varargs.vararg
                kwonlyargs = args_varargs.kwonlyargs
                kw_defaults = args_varargs.kw_defaults
                kwarg = args_varargs.kwarg

    return ast.Arguments(tuple(args), vararg, kwonlyargs, kw_defaults, kwarg, tuple(defaults))

def emit_simple_stmt(args):
    first_stmt, remainder, opt_colon, newline = unpack_n(args, 4)
    if remainder != '':
        all_stmts = (first_stmt,) + tuple(s for c, s in remainder)
    else:
        all_stmts = first_stmt

    return all_stmts

def emit_test_left(args):
    or_test, opt_if = args
    if opt_if == '':
        return or_test
    _, cond, _, orelse = opt_if
    return ast.IfExp(cond, or_test, orelse)

def emit_test_list_star_expr(args):
    test_or_star, opt_following_test_or_star, opt_trailing_comma = unpack_n(args, 3)
    if opt_following_test_or_star != '':
        _, exprs = zip(*opt_following_test_or_star)
        return (test_or_star,) + exprs
    return test_or_star

def emit_test_list(args):
    first, remainder, opt_trail = unpack_n(args, 3)
    if remainder == '':
        print('TL',[first])
        return first
    _, following = zip(*remainder)
    return ast.Tuple((first,) + following)

def emit_expr_augassign(args):
    test_list, augassign, yield_or_test_list = unpack_n(args, 3)
    first_expr, *remainder = test_list
    if remainder:
        raise SyntaxError("Invalid multiple assignments for augassign")

    lit_to_op = {'+=': ast.OperatorType.Add,
                 '-=': ast.OperatorType.Sub,
                 '*=': ast.OperatorType.Mult,
                 '/=': ast.OperatorType.Div,
                 '//=': ast.OperatorType.FloorDiv,
                 '@=': ast.OperatorType.MatMult,
                 '<<=': ast.OperatorType.LShift,
                 '>>=': ast.OperatorType.RShift,
                 '|=': ast.OperatorType.BitOr,
                 '&=': ast.OperatorType.BitAnd,
                 '^=': ast.OperatorType.BitXOr,
                 '**=': ast.OperatorType.Pow}
    return ast.AugAssign(first_expr, lit_to_op[augassign], yield_or_test_list)

def emit_or_test(args):
    and_test, or_and_tests = args
    if or_and_tests == '':
        return and_test

    _, further_ands = zip(*or_and_tests)
    return ast.BoolOp(ast.BoolOpType.Or, (and_test,)+further_ands)

def emit_not_test(args):
    _, test = args
    return ast.UnaryOp(ast.UnaryOpType.Not, test)

def emit_and_test(args):
    not_test, and_not_tests = args
    if and_not_tests == '':
        return not_test

    _, further_nots = zip(*and_not_tests)
    return ast.BoolOp(ast.BoolOpType.And, (not_test,)+further_nots)


def emit_expr_assigns(args):
    test_list, assignments = args

    if assignments == '':
        return test_list

    if isinstance(test_list, ast.AstNode):
        test_list = test_list,

    _, (*exprs, value) = zip(*assignments)
    return ast.Assign(test_list+tuple(exprs), value)

def emit_comparison(args):
    expr, comp_exprs = args

    if comp_exprs == '':
        return expr

    op_table = {'==': ast.ComparisonOpType.Eq, '!=': ast.ComparisonOpType.NotEq, '>': ast.ComparisonOpType.Gt,
                '<': ast.ComparisonOpType.Lt, '>=': ast.ComparisonOpType.GtE, '<=': ast.ComparisonOpType.LtE,
                'is': ast.ComparisonOpType.Is, ('is','not'): ast.ComparisonOpType.IsNot,
                ('not', 'in'): ast.ComparisonOpType.Gt, 'in': ast.ComparisonOpType.In}
    ops, comparators = zip(*comp_exprs)
    op_enums = tuple(op_table[o] for o in ops)
    return ast.Compare(expr, op_enums, comparators)

def emit_expr(args):
    xor, opt_xors = args
    if opt_xors == '':
        return xor
    left = xor
    for _, right in opt_xors:
        left = ast.BinOp(left, ast.OperatorType.BitOr, right)
    return left

def emit_xor_expr(args):
    and_expr, opt_xor_exprs = args
    if opt_xor_exprs == '':
        return and_expr

    left = and_expr
    for _, right in opt_xor_exprs:
        left = ast.BinOp(left, ast.OperatorType.BinXOr, right)
    return left

def emit_and_expr(args):
    shift_expr, opt_shift_exprs = args
    if opt_shift_exprs == '':
        return shift_expr
    left = shift_expr
    for _, right in opt_shift_exprs:
        left = ast.BinOp(left, ast.OperatorType.BitAnd, right)
    return left

def emit_shift_expr(args):
    arith_expr, opt_shift_exprs = args
    if opt_shift_exprs == '':
        return arith_expr

    op_table = {'>>': ast.OperatorType.RShift, '<<': ast.OperatorType.LShift}

    left = arith_expr
    for shift_expr, right in opt_shift_exprs:
        left = ast.BinOp(left, op_table[shift_expr], right)
    return left

def emit_arith_exor(args):
    term, opt_ariths = args
    if opt_ariths == '':
        return term

    op_table = {'+': ast.OperatorType.Add, '-': ast.OperatorType.Sub}

    left = term
    for arith_op, right in opt_ariths:
        left = ast.BinOp(left, op_table[arith_op], right)
    return left

def emit_term(args):
    factor, opt_terms = args
    if opt_terms == '':
        return factor

    op_table = {'*': ast.OperatorType.Mult,
                '/': ast.OperatorType.Div,
                '%': ast.OperatorType.Mod,
                '//': ast.OperatorType.FloorDiv,
                '@': ast.OperatorType.MatMult}

    left = factor
    for term_op, right in opt_terms:
        left = ast.BinOp(left, op_table[term_op], right)
    return left

def emit_factor(args):
    op, factor = args
    op_table = {'+': ast.UnaryOpType.UAdd, '-': ast.UnaryOpType.USub, '~': ast.UnaryOpType.Invert}
    return ast.UnaryOp(op_table[op], factor)

def emit_power(args):
    atom, opt_factor = args
    if opt_factor == '':
        return atom
    _, exponent = opt_factor
    return ast.BinOp(atom, ast.OperatorType.Pow, exponent)

def emit_id(value):
    return ast.Name(value)

def emit_arg_list(args):
    arg, opt_args, opt_comma = unpack_n(args, 3)
    if opt_args == '':
        return arg,
    commas, following_args = zip(*opt_args)
    return (arg,) + following_args

def emit_kwargs(args):
    _, arg = args
    return ast.Keyword(None, arg)

def emit_starred(args):
    _, arg = args
    return ast.Starred(arg)

def emit_nl_indented(args):
    _, _, stmts, _ = unpack_n(args, 4)
    return stmts

def emit_file_input(args):
    nl_or_stmts, _ = args
    if nl_or_stmts == '':
        return ()
    return ast.Module(nl_or_stmts)

def args_list_to_args_kwargs(arg_list):
    args = []
    keywords = []
    for arg in arg_list:
        if isinstance(arg, ast.Keyword):
            keywords.append(arg)
        else:
            if keywords:
                raise SyntaxError("Positional arg after keyword arg")
            args.append(arg)
    return tuple(args), tuple(keywords)

def emit_class_def(args):
    _, cls_name, opt_args, _, body = unpack_n(args, 5)
    if opt_args == '':
        bases = ()
        keywords = ()
    else:
        _, arg_list, _ = unpack_n(opt_args, 3)
        bases, keywords = args_list_to_args_kwargs(arg_list)
    return ast.ClassDef(cls_name, bases, keywords, body, ())

def emit_keyword(args):
    name, _, value = unpack_n(args, 3)
    return ast.Keyword(name, value)

def emit_arg(args):
    name, opt_comp_for = args
    if opt_comp_for == '':
        return name

    return args

def emit_comp_for(args):
    _, expr_list, _, or_test, opt = unpack_n(args, 5)
    if opt == '':
        opt = None
    return ast.CompFor(expr_list, or_test, opt)

def emit_comp_if(args):
    _, cond, opt = unpack_n(args, 3)
    if opt == '':
        opt = None

    return ast.CompIf(cond, opt)

def emit_yield_expr(args):
    _, opt_arg = args
    if opt_arg == '':
        opt_arg = None
    return ast.Yield(opt_arg)

def emit_num(num):
    return ast.Num(num)

def emit_atom_expr(args):
    atom, trailers = args
    if trailers == '':
        return atom

    node = atom

    for trailer in trailers:
        # XXX do this more efficiently?
        body, end_char = trailer
        if end_char == ']':
            _, opt_slice = body
            node = ast.Subscript(node, opt_slice)

        elif end_char == ')':
            _, arg_list = body

            arguments, keywords = args_list_to_args_kwargs(arg_list)
            node = ast.Call(node, arguments, keywords)

        else:
            node = ast.Attribute(node, end_char)

    return node

def emit_expr_list(args):
    root_expr, opt_com_del_exprs, opt_trail = unpack_n(args, 3)
    if opt_com_del_exprs == '':
        return root_expr

    commas, exprs = zip(*opt_com_del_exprs)
    return exprs

g = GrammarFactory()

g.single_input = (ter('NEWLINE') | g.simple_stmt | g.compound_stmt) & ter('NEWLINE')
# g.eval_input = g.test_list & +ter('NEWLINE') & ter('ENDMARKER')
g.file_input = (+(ter('NEWLINE') | g.stmt) & ter('ENDMARKER')) >> emit_file_input

g.decorator = ter('@') & g.dotted_name & ~(ter('(') & ~g.arg_list & ter(')')) & ter('NEWLINE')
g.decorators = one_plus(g.decorator)
g.decorated = g.decorators & (g.class_def | g.func_def)  # Ignore async

g.func_def = (ter('def') & ter('ID') & g.parameters & ~(ter('->') & g.test) & ter(':') & g.suite) >> emit_func_def


def generate_args_list(tfpdef):
    tfpdef_opt_ass = tfpdef & ~(ter('=') & g.test)
    tfpdef_kwargs = ter('**') & tfpdef
    return ((tfpdef_opt_ass & +(ter(',') & tfpdef_opt_ass) & ~(ter(',') & ~((ter('*') & ~tfpdef & +(ter(',') & tfpdef_opt_ass) & ~(ter(',') & tfpdef_kwargs)) | tfpdef_kwargs))) >> emit_first |
            (ter('*') & ~tfpdef & +(ter(',') & tfpdef_opt_ass) & ~(ter(',') & tfpdef_kwargs)) >> emit_varargs |
            tfpdef_kwargs >> emit_kwargs_only)

g.parameters = (ter('(') & ~g.typed_args_list & ter(')')) >> emit_params

g.typed_args_list = generate_args_list(g.tfpdef)
g.tfpdef = (ter('ID') & ~(ter(':') & g.test)) >> emit_tfpdef

g.var_args_list = generate_args_list(g.vfpdef)
g.vfpdef = ter('ID')

# TODO how to discern between lists and single values
g.stmt = g.simple_stmt | g.compound_stmt

g.simple_stmt = (g.small_stmt & +(ter(';') & g.small_stmt) & ~ter(';') & ter('NEWLINE')) >> emit_simple_stmt
g.small_stmt = (g.expr_stmt | g.del_stmt | g.pass_stmt | g.flow_stmt | g.import_stmt | g.global_stmt | g.nonlocal_stmt | g.assert_stmt)
g.expr_stmt = (g.test_list_star_expr & g.augassign & (g.yield_expr | g.test_list)) >> emit_expr_augassign | \
              (g.test_list_star_expr & +(ter('=') & (g.yield_expr | g.test_list_star_expr))) >> emit_expr_assigns
g.test_list_star_expr = ((g.test | g.star_expr) & +(ter(',') & (g.test | g.star_expr)) & ~ter(',')) >> emit_test_list_star_expr
g.augassign = ter('+=') | ter('-=') | ter('*=') | ter('/=') | ter('%=') | ter('&=') | ter('|=') | ter('^=') | ter('^=') \
              | ter('<<=') | ter('>>=') | ter('**=') | ter('//=') | ter('@=')
g.del_stmt = ter('del') & g.expr_list >> emit_del
g.pass_stmt = ter('pass') >> emit_pass
g.flow_stmt = g.break_stmt | g.continue_stmt | g.return_stmt | g.raise_stmt | g.yield_stmt
g.break_stmt = ter('break') >> emit_break
g.continue_stmt = ter('continue') >> emit_continue
g.return_stmt = (ter('return') & ~g.test_list) >> emit_return
g.yield_stmt = g.yield_expr

g.raise_stmt = (ter('raise') & ~(g.test & ~(ter('from') & g.test))) >> emit_raise
g.import_stmt = g.import_name | g.import_from
g.import_name = (ter('import') & g.dotted_as_names) >> emit_import
g.import_from = (ter('from') &
                 ((+(ter('.') | ter('...')) & g.dotted_name) >> emit_import_from_dotted_name
                                | one_plus(ter('.') | ter('...')) >> emit_import_from_no_name
                                )
                 & ter('import') &
                 (ter('*') >> emit_import_from_all | (ter('(') & g.import_as_names & ter(')')) >> emit_import_from_names_paren | g.import_as_names >> emit_import_from_names)) >> emit_import_from
g.import_as_name = (ter('ID') & ~(ter('as') & ter('ID'))) >> emit_import_as_name
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
g.try_stmt = (ter('try') & ter(':') & g.suite &
             ((one_plus(g.except_clause & ter(':') & g.suite) &
               ~(ter('else') & ter(':') & g.suite) &
               ~(ter('finally') & ter(':') & g.suite)) |
              # Just finally no except
              (ter('finally') & ter(':') & g.suite)
              )) >> emit_try
g.with_stmt = (ter('with') & g.with_item & +(ter(',') & g.with_item) & ter(':') & g.suite) >> emit_with
g.with_item = g.test & ~(ter('as') & g.expr)
g.except_clause = ter('except') & ~(g.test & ~(ter('as') & ter('ID')))
g.suite = g.simple_stmt | (ter('NEWLINE') & ter('INDENT') & one_plus(g.stmt) & ter('DEDENT')) >> emit_nl_indented
g.test = (g.or_test & ~(ter('if') & g.or_test & ter('else') & g.test)) >> emit_test_left | g.lambda_def
g.test_no_cond = g.or_test | g.lambda_def_no_cond

g.lambda_def = (ter('lambda') & ~g.var_args_list & ter(':') & g.test) >> emit_lambda_def
g.lambda_def_no_cond = ter('lambda') & ~g.var_args_list & ter(':') & g.test_no_cond >> emit_lambda_def
g.or_test = (g.and_test & +(ter('or') & g.and_test)) >> emit_or_test
g.and_test = (g.not_test & +(ter('and') & g.not_test)) >> emit_and_test
g.not_test = (ter('not') & g.not_test) >> emit_not_test | g.comparison
g.comparison = (g.expr & +(g.comp_op & g.expr)) >> emit_comparison

g.comp_op = ter('<') | ter('>') | ter('==') | ter('>=') | ter('<=') | ter('<>') | ter('!=') | ter('in') | ter(
    'not') & ter('in') | ter('is') | ter('is') & ter('not')
g.star_expr = ter('*') & g.expr
g.expr = (g.xor_expr & +(ter('|') & g.xor_expr)) >> emit_expr

g.xor_expr = (g.and_expr & +(ter('^') & g.and_expr)) >> emit_xor_expr
g.and_expr = (g.shift_expr & +(ter('&') & g.shift_expr)) >> emit_and_expr
g.shift_expr = (g.arith_expr & +((ter('<<') | ter('>>')) & g.arith_expr)) >> emit_shift_expr
g.arith_expr = (g.term & +((ter('+') | ter('-')) & g.term)) >> emit_arith_exor
g.term = (g.factor & +((ter('*') | ter('@') | ter('/') | ter('%') | ter('//')) & g.factor)) >> emit_term
g.factor = ((ter('+') | ter('-') | ter('~')) & g.factor) >> emit_factor | g.power
g.power = (g.atom_expr & ~(ter('**') & g.factor)) >> emit_power

def emit_list_comp(args):
    _, body, _ = unpack_n(args, 3)
    if body == '':
        return ast.List(())
    return body

def emit_test_list_comp(args):
    test_or_stexpr, comp_for_or_list_of_comma_test_or_stexpr = args

    if isinstance(comp_for_or_list_of_comma_test_or_stexpr, ast.CompFor):
        return ast.ListComp(test_or_stexpr, comp_for_or_list_of_comma_test_or_stexpr)

    else:
        exprs = (test_or_stexpr,) + comp_for_or_list_of_comma_test_or_stexpr
        return ast.List(exprs)

g.atom_expr = (g.atom & +g.trailer) >> emit_atom_expr
g.atom = ((ter('(') & ~(g.yield_expr | g.test_list_comp) & ter(')')) |#>> emit_generator_comp |
          (ter('[') & ~(g.yield_expr | g.test_list_comp) & ter(']')) >> emit_list_comp |
          (ter('{') & ~g.dict_or_set_maker & ter('}')) |#>> emit_dict_comp |
          ter('ID') >> emit_id | ter('NUMBER') >> emit_num | one_plus(ter('LIT')) | ter('...') | ter('None') | ter('True') | ter('False'))

def emit_list_exprs(args):
    list_exprs, opt_comma = args
    if list_exprs == '':
        return ()
    commas, exprs = zip(*list_exprs)
    return exprs

g.test_list_comp = ((g.test | g.star_expr) & (g.comp_for | (+(ter(',') & (g.test | g.star_expr)) & ~ter(','))>> emit_list_exprs)) >> emit_test_list_comp
g.trailer = (ter('(') & ~g.arg_list & ter(')')) | (ter('[') & g.subscript_list & ter(']')) | (ter('.') & ter('ID'))
g.arg_list = (g.argument & +(ter(',') & g.argument) & ~ter(',')) >> emit_arg_list
g.subscript_list = g.subscript & +(ter(',') & g.subscript) & ~ter(',')
g.subscript = g.test | (~g.test & ter(':') & ~g.test & ~g.slice_op)
g.slice_op = ter(':') & ~g.test
g.expr_list = ((g.expr | g.star_expr) & +(ter(',') & (g.expr | g.star_expr)) & ~ter(',')) >> emit_expr_list
g.test_list = (g.test & +(ter(',') & g.test) & ~ter(',')) >> emit_test_list
g.dict_or_set_maker = (((g.test & ter(':') & g.test) | (ter('**') & g.expr) &
                        (
                        g.comp_for | +(ter(',') & ((g.test & ter(':') & g.test) | (ter('**') & g.expr))) & ~ter(','))) |
                       ((g.test | g.star_expr) & (g.comp_for | +(ter(',') & (g.test | g.star_expr)) & ~ter(','))))


g.argument = ((g.test & ~g.comp_for) >> emit_arg |
              (g.test & ter('=') & g.test) >> emit_keyword |
              (ter('**') & g.test) >> emit_kwargs |
              (ter('*') & g.test) >> emit_starred)
g.comp_iter = g.comp_for | g.comp_if

# TODO rename "_list" construct to something else if can return tuple or single value
g.class_def = (ter('class') & ter('ID') & ~(ter('(') & ~g.arg_list & ter(')')) & ter(':') & g.suite) >> emit_class_def

g.comp_for = (ter('for') & g.expr_list & ter('in') & g.or_test & ~g.comp_iter) >> emit_comp_for
g.comp_if = (ter('if') & g.test_no_cond & ~g.comp_iter) >> emit_comp_if

g.yield_expr = (ter('yield') & ~g.yield_arg) >> emit_yield_expr
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
        from ast import print_ast
        module = result.pop()
        print('parse', module)
        module.body[0].names += (ast.Ellipsis_(),)
        ast.print_ast(module)