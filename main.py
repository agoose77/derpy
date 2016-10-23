from collections import namedtuple
from tokenize import generate_tokens
import token
from keyword import iskeyword

from silk_ast import *
from derp import parse, to_text, ter, empty_string, flatten_first, flatten_last, Recurrence, BaseParser


Token = namedtuple("Token", "first second")


def convert_token(tok_info):
    if tok_info.type == token.NAME:
        value = tok_info.string
        if iskeyword(value):
            return Token(value, value)

        else:
            return Token('ID', tok_info.string)

    elif tok_info.type == token.STRING:
        return Token('LIT', eval(tok_info.string))

    elif tok_info.type == token.NUMBER:
        return Token('NUMBER', tok_info.string)

    elif tok_info.type == token.NEWLINE:
        return Token("NEWLINE", "NEWLINE")

    elif tok_info.type == token.INDENT:
        return Token("INDENT", "INDENT")

    elif tok_info.type == token.INDENT:
        return Token("DEDENT", "DEDENT")

    elif tok_info.type == token.ERRORTOKEN:
        return Token("ERROR", tok_info.string)

    elif tok_info.type == token.ENDMARKER:
        return Token("ENDMARKER", "ENDMARKER")

    else:
        return Token(tok_info.string, tok_info.string)


class GrammarFactory:

    def __init__(self):
        object.__setattr__(self, '_recurrences', {})

    def validate(self):
        for name, parser in self._recurrences.items():
            if parser.parser is None:
                raise ValueError("{} parser is not defined".format(name))

    def __getattr__(self, name):
        result = Recurrence()
        self._recurrences[name] = result
        object.__setattr__(self, name, result) # To stop this being created again
        return result

    def __setattr__(self, name, value):
        assert isinstance(value, BaseParser), (name, value)

        # Existing parser is either recurrence or non recurrence
        if hasattr(self, name):
            if name in self._recurrences:
                recurrence = getattr(self, name)
                if recurrence.parser is not None:
                    raise ValueError('Recurrent parser already defined')

                recurrence.parser = value
            else:
                raise ValueError('Parser already assigned')

        # No recurrence relation (as assignment BEFORE get)
        else:
            object.__setattr__(self, name, value)


def w(f):
    def wrapper(args):
        print("DBG",f.__qualname__)
        return f(args)
    return wrapper


g = GrammarFactory()


def emit_program(args):
    return args

g.file_input = (g.lines & ter('ENDMARKER')) >> emit_program

def emit_nl(args):
    print('A',args)
    return args

def emit_line(args):
    print('L', args)
    return args

g.lines = ~((ter('NEWLINE') & g.lines) >> emit_nl | (g.stmt & g.lines) >> emit_line)

def emit_func_def(args):
    _, name, params, _ = flatten_first(args)
    print("FUNC DEF", name, params)
    return "<def {}{}>".format(name, params)
g.func_def = (ter('def') & ter('ID') & g.parameters & ter(':') & g.suite) >> emit_func_def

def emit_params(args):
    _, params, _ = flatten_first(args)
    return params
g.parameters = (ter('(') & g.zero_plus_params & ter(')')) >> emit_params

def emit_param_list(args):
    return args

def emit_rest_of_params(args):
    _, name, _ = flatten_first(args)
    return name


def ep(args):
    return ''.join(unpack_n(args, 3))

def eas(args):
    return "<={}>".format(args[1])
def etyp(args):
    col, tid = args
    return "<:{}>".format(tid)
def epars(args):
    return args

g.rest_of_ids = empty_string | (ter(',') & ter('ID') & g.rest_of_ids) >> emit_rest_of_params

g.zero_plus_params = empty_string | (ter('ID') & g.rest_of_ids) >> emit_param_list | ter(',')#~(((ter('ID') & g.rest_of_ids) >> emit_param_list) | ter(','))


def emit_small_stmts(args):
    return args

g.more_small_stmts = (ter(';') & g.small_stmt & g.more_small_stmts) >> emit_small_stmts
zero_plus_small_stmts = +g.more_small_stmts
end_of_stmts = empty_string & ter('NEWLINE') | (ter(';') & ter('NEWLINE'))


g.stmt.parser = g.simple_stmt | g.compound_stmt
g.simple_stmt.parser = g.small_stmt & zero_plus_small_stmts & end_of_stmts


g.small_stmt.parser = g.expr_stmt | g.del_stmt | g.pass_stmt | g.flow_stmt | g.global_stmt | g.nonlocal_stmt | g.assert_stmt

g.augassign = ter('+=') | ter('-=') | ter('*=') | ter('/=') | ter('%=') | ter('&=') | ter('|=') | ter('^=') | ter('^=') \
            | ter('<<=') | ter('>>=') | ter('**=') | ter('//=')

def emit_aug_assign_stmt(args):
    return args
def emit_assign_stmt(args):
    return args
def emit_expr_stmt(args):
    return args
g.expr_stmt = (g.many_tests & g.augassign & g.many_tests) >> emit_aug_assign_stmt | \
                     (g.many_tests & ter('=') & g.test_or_tests) >> emit_assign_stmt | \
                     g.test_or_tests >> emit_expr_stmt


def emit_del_stmt(args):
    return args
g.del_stmt = (ter('del') & g.star_expr) >> emit_del_stmt

def emit_pass_stmt(args):
    return args
g.pass_stmt = ter('pass') >> emit_pass_stmt

g.flow_stmt = g.break_stmt | g.continue_stmt | g.return_stmt | g.raise_stmt

def emit_break_stmt(args):
    return args
g.break_stmt = ter('break') >> emit_break_stmt

def emit_continue_stmt(args):
    return args
g.continue_stmt = ter('continue') >> emit_continue_stmt
g.return_expr = ~g.many_tests

def emit_from_stmt(args):
    return args
g.raise_from = ~((ter('from') & g.test) >> emit_from_stmt)

def emit_raise_new_exception(args):
    return args
g.raise_clause = ~((g.test & g.raise_from) >> emit_raise_new_exception)
g.return_stmt = ter('return') & g.return_expr >> emit_continue_stmt

def emit_raise_stmt(args):
    return args
g.raise_stmt = (ter('raise') & g.raise_clause) >> emit_raise_stmt

def emit_rest_of_ids(args):
    return args
g.zero_plus_ids = ~((ter(',') & ter('ID') & g.zero_plus_ids) >> emit_rest_of_ids)
def emit_global_stmt(args):
    return args
g.global_stmt = (ter('global') & ter('ID') & g.zero_plus_ids) >> emit_global_stmt
def emit_nonlocal_stmt(args):
    return args
g.nonlocal_stmt = (ter('nonlocal') & ter('ID') & g.zero_plus_ids) >> emit_nonlocal_stmt
def emit_rest_of_tests(args):
    return args
zero_plus_tests = ~((ter(',') & g.test) >> emit_rest_of_tests)
def emit_assert_stmt(args):
    return args
g.assert_stmt = (ter('assert') & g.test & zero_plus_tests) >> emit_assert_stmt
g.compound_stmt = g.if_stmt | g.while_stmt | g.for_stmt | g.try_stmt | g.func_def

def emit_elifs(args):
    return args

g.zero_or_more_elifs = ~((ter('elif') & g.test & ter(':') & g.suite & g.zero_or_more_elifs) >> emit_elifs)
def emit_else_clause(args):
    return args

g.else_clause = ~((ter('else') & ter(':') & g.suite) >> emit_else_clause)
g.if_stmt = (ter('if') & g.test & ter(':') & g.suite & (g.zero_or_more_elifs & g.else_clause))

def emit_while_else_clause(args):
    return args
g.while_else_clause = ~((ter('else') & ter(':') & g.suite) >> emit_while_else_clause)

def emit_while_stmt(args):
    return args
g.while_stmt = (ter('while') & g.test & ter(':') & g.suite & g.while_else_clause) >> emit_while_stmt

def emit_for_else_clause(args):
    return args
g.for_else_clause = ~((ter('else') & ter(':') & g.suite) >> emit_for_else_clause)
def emit_for_stmt(args):
    return args
g.for_stmt = (ter('for') & ter('ID') & ter('in') & g.test & ter(':') & g.suite & g.for_else_clause) >> emit_for_stmt

def emit_finally_try_block(args):
    return args
g.finally_try_block = (ter('finally') & ter(':') & g.suite) >> emit_finally_try_block


def emit_except_vars(args):
    return args
g.except_vars = ~((ter('as') & ter('ID')) >> emit_except_vars)

def emit_except_type(args):
    return args
g.except_type = ~((g.test & g.except_vars) >> emit_except_type)
g.except_clause = (ter('except') & g.except_type)

def emit_except_else_clause(args):
    return args
g.except_else_clause = ~((ter('else') & ter(':') & g.suite) >> emit_except_else_clause)

def emit_finally_catch_block(args):
    return args
g.finally_catch_block = ~((ter('finally') & ter(':') & g.suite) >> emit_finally_catch_block)

def emit_fail_if_not_parsed(args):
    return args

g.else_block = g.except_else_clause >> emit_fail_if_not_parsed
g.finally_block = g.finally_catch_block >> emit_fail_if_not_parsed

def emit_except_clauses(args):
    return args
g.zero_plus_excepts = ~((g.except_clause & ter(':') & g.suite & g.zero_plus_excepts) >> emit_except_clauses)

def emit_except_else_finally(args):
    return args
g.catch_and_finally_blocks = (g.except_clause & ter(':') & g.suite & g.zero_plus_excepts & g.else_block & g.finally_block) >> emit_except_else_finally

g.exception_handlers = g.catch_and_finally_blocks | g.finally_try_block
def emit_try_stmt(args):
    return args
g.try_stmt = (ter('try') & ter(':') & g.suite & g.exception_handlers) >> emit_try_stmt

def emit_stmts(args):
    return args

g.one_plus_stmts = (g.stmt & g.zero_plus_stmts) >> emit_stmts
g.zero_plus_stmts = ~g.one_plus_stmts

def emit_suite(args):
    return args
g.suite = g.simple_stmt | ((ter('NEWLINE') & ter('INDENT') & g.one_plus_stmts & ter('DEDENT')) >> emit_suite)

g.comparison_operator = ter('<') | ter('>') | ter('==') | ter('>=') | ter('<=') | ter('<>') | ter('!=')

def emit_comparison_operator(args):
    return args
def emit_not_in(args):
    return args
def emit_is_not(args):
    return args
g.comparison_type = g.comparison_operator >> emit_comparison_operator | ter('in') | ter('is') |\
             (ter('not') & ter('in')) >> emit_not_in | (ter('is') & ter('not')) >> emit_is_not

def emit_comparison(args):
    star_expr, any_comps = args
    if any_comps == '':
        return star_expr
    print("COMP", star_expr, [any_comps])
    return args
g.comparison = (g.star_expr & g.zero_plus_comps) >> emit_comparison

def emit_zero_plus_comps(args):
    return args
g.zero_plus_comps = ~((g.comparison_type & g.star_expr & g.zero_plus_comps) >> emit_zero_plus_comps)

def emit_lambda_def(args):
    return args
g.lambdef = (ter('lambda') & g.zero_plus_params & ter(':') & g.test) >> emit_lambda_def

def emit_not_test(args):
    _, not_test = args
    print("NOT", not_test)
    return not_test
g.not_test = (ter('not') & g.not_test) >> emit_not_test | g.comparison
g.zero_plus_nots = ~((ter('and') & g.not_test & g.zero_plus_nots))

def emit_and_test(args):
    not_test, any_nots = args
    if any_nots == '':
        return not_test
    print("AND", not_test, [any_nots])
    return args
g.and_test = (g.not_test & g.zero_plus_nots) >> emit_and_test

def emit_zero_plus_ors(args):
    return args
g.zero_plus_ors = ~((ter('or') & g.and_test & g.zero_plus_ors) >> emit_zero_plus_ors)

def emit_or_test(args):
    and_test, any_ors = args
    if any_ors == '':
        return and_test
    print("OR", and_test, [any_ors])
    return args
g.or_test = (g.and_test & g.zero_plus_ors) >> emit_or_test

def emit_test(args):
    ortest1, _, ortest2, _, test_exp = unpack_n(args, 5)
    return ('TEST@',ortest1, ortest2, test_exp)

g.test = g.or_test | ((g.or_test & ter('if') & g.or_test & ter('else') & g.test) >> emit_test) | g.lambdef

def emit_expr(args):
    xor, any_xors = args
    if any_xors == '':
        return xor
    print("EXPR", xor, [any_xors])
    return args
g.expr = (g.xor_expr & g.zero_plus_xors) >> emit_expr

def emit_star_expr(args):
    opt_star, expr = args
    if opt_star == '':
        return expr
    print("MUL")
    return StarExpr(expr)

g.star_expr = (~ter('*') & g.expr) >> emit_star_expr

def emit_xor_expr(args):
    and_exp, any_ands = args
    if any_ands == '':
        return and_exp
    print("XOR_EXP", and_exp, [any_ands])
    return args
g.xor_expr = (g.and_expr & g.zero_plus_ands) >> emit_xor_expr

def emit_zero_plus_xors(args):
    return args
g.zero_plus_xors = ~((ter('|') & g.xor_expr & g.zero_plus_xors) >> emit_zero_plus_xors)

def emit_and_expr(args):
    shift_exp, any_shifts = args
    if any_shifts == '':
        return shift_exp

    print("AND_EXP", shift_exp, [any_shifts])
    return args
g.and_expr = (g.shift_expr & g.zero_plus_shifts) >> emit_and_expr

def emiz_zero_plus_ands(args):
    return args
g.zero_plus_ands = ~((ter('^') & g.and_expr & g.zero_plus_ands) >> emiz_zero_plus_ands)

def emit_shift_expr(args):
    arith, any_ariths = args
    if any_ariths == '':
        return arith
    print("shift_expr", arith, [any_ariths])
    return args
g.shift_expr = (g.arith_expr & g.zero_plus_arith_exprs) >> emit_shift_expr

def emit_zero_plus_shifts(args):
    return args
g.zero_plus_shifts = ~((ter('&') & g.shift_expr & g.zero_plus_shifts) >> emit_zero_plus_shifts)

def emit_arith_expr(args):
    term, any_adds = args
    if any_adds == '':
        return term
    print("ARITH", term, [any_adds])#TODO
    return args
g.arith_expr = (g.term & g.zero_plus_adds) >> emit_arith_expr

def emit_zero_plus_arith_exprs(args):
    return args
g.zero_plus_arith_exprs = ~(((ter('<<') | ter('>>')) & g.arith_expr & g.zero_plus_arith_exprs) >> emit_zero_plus_arith_exprs)

def emit_zero_plus_adds(args):
    return args
g.zero_plus_adds = ~(((ter('+') | ter('-')) & g.term & g.zero_plus_adds) >> emit_zero_plus_adds)

def emit_term(args):
    factor, any_mults = args
    if any_mults == '':
        return factor
    return TermNode()
    print("TERM", factor, [any_mults])
    return args
g.term = (g.factor & g.zero_plus_mults) >> emit_term

g.operator = ter('*') | ter('/') | ter('%') | ter('//')

def emit_zero_plus_mults(args):
    (op, factor), tail = args
    print("ZEROPLUS", op, factor, tail)
    return args
g.zero_plus_mults = ~((g.operator & g.factor & g.zero_plus_mults) >> emit_zero_plus_mults)

g.operator_choice = ter('+') | ter('-') | ter('~')
def emit_factor(args):
    choice, factor = args
    print("FACTOPR", choice,factor)
    return args
g.factor = g.power | ((g.operator_choice & g.factor) >> emit_factor)

def emit_exponent(args):
    _, fact = args
    return fact
g.exponent = ~((ter('*') & g.factor) >> emit_exponent)

def emit_indexed(args):
    atom, trailers = args
    if trailers == '':
        return atom
    print(args)
    return args
g.indexed = (g.atom & g.zero_plus_trailers) >> emit_indexed

def emit_power(args):
    indexed, exponent = args
    print("EM",args)
    if exponent == '':
        return indexed
    return PowerNode(indexed, exponent)
g.power = (g.indexed & g.exponent) >> emit_power

# Atom
def emit_id(args):
    return args

def emit_dots(args):
    return args
g.atom = (g.tuple | g.list | g.dict | ter('ID') >> emit_id | ter('NUMBER') | g.string |
            ter('...') >> emit_dots | ter('None') | ter('True') | ter('False'))

# Tuple
def emit_tuple(args):
    _, value, _ = flatten_first(args)
    return TupleNode(value)
g.tuple = (ter('(') & ~g.test_or_tests & ter(')')) >> emit_tuple


#List
def emit_list(args):
    _, tests, _ = unpack_n(args, 3)
    return ListNode(tests)
g.list = (ter('[') & ~g.many_tests & ter(']')) >> emit_list

from derp import unpack_n

# Dict
def emit_dict(args):
    _, dict_or_set_maker_opt, _ = unpack_n(args, 3)
    return dict_or_set_maker_opt
g.dict = (ter('{') & ~g.dict_or_set_maker & ter('}')) >> emit_dict


# String
def emit_string(args):
    string1, remainder = args
    if remainder == '':
        return StringNode(string1)
    return StringNode(string1+remainder.value)

g.string = (ter('LIT') & g.zero_plus_strs) >> emit_string
g.zero_plus_strs = ~((ter('LIT') & g.zero_plus_strs) >> emit_string)

def emit_trailer_tuple(args):
    return args
def emit_subscript(args):
    return args
def emit_method_call(args):
    return args
g.method_call = ter('.') & ter('ID')
g.subscript = ter('[') & g.test_or_tests & ter(']')
g.trailer = (ter('(') & ~g.arg_list & ter(')')) >> emit_trailer_tuple | g.subscript >> emit_subscript | g.method_call >> emit_method_call

def emit_zero_plus_trailers(args):
    return args
g.zero_plus_trailers = ~((g.trailer & g.zero_plus_trailers) >> emit_zero_plus_trailers)

def emit_many_tests(args):
    test, test_tuple, _ = unpack_n(args, 3)
    if test_tuple == '':
        return test,
    return (test,) + test_tuple

g.many_tests = (g.test & g.test_tuple & ~ter(',')) >> emit_many_tests
def emit_test_or_tests(args):
    first, remainder, _ = unpack_n(args, 3)
    if remainder == '':
        return first,
    return (first,) + remainder

g.test_or_tests = (g.test & g.zero_plus_args & ~ter(',')) >> emit_test_or_tests

g.dict_or_set_maker = g.dict_maker | g.set_maker

def emit_dict_maker(args):
    key, _, val, rest_of_dict, _ = unpack_n(args, 5)
    if rest_of_dict == '':
        return DictNode((key,), (val,))

    return DictNode(rest_of_dict.keys+(key,),
                    rest_of_dict.values+(val,))
g.dict_maker = (g.test & ter(':') & g.test & g.test_tuple_prime & ~ter(',')) >> emit_dict_maker

def emit_set_maker(args):
    return args
g.set_maker = (g.test & g.test_tuple & ~ter(',')) >> emit_set_maker

def emit_test_tuple(args):
    _, test, test_tuple = unpack_n(args, 3)
    if test_tuple == '':
        return test,
    return (test,) + test_tuple

g.test_tuple = ~((ter(',') & g.test & g.test_tuple) >> emit_test_tuple)

def emit_test_tuple_prime(args):
    _, key, _, val, rest_of_tests = unpack_n(args, 5)

    if rest_of_tests != '':
        keys = rest_of_tests.keys + key,
        vals = rest_of_tests.vals + val,
    else:
        keys = key,
        vals = val,

    return args#DictNode(keys, vals)

    return ((test1, test2),) + rest_of_tests#TODO
g.test_tuple_prime = ~((ter(',') & g.test & ter(':') & g.test & g.test_tuple_prime) >> emit_test_tuple_prime)

def emit_arg_list(args):
    return args
g.arg_list = (g.test & g.zero_plus_args & ~ter(',')) >> emit_arg_list

def emit_zero_plus_args(args):
    _, test, remainder = unpack_n(args, 3)
    if remainder == '':
        return (test,)
    return (test,) + remainder

g.zero_plus_args = ~((ter(',') & g.test & g.zero_plus_args) >> emit_zero_plus_args)

g.validate()


if __name__ == "__main__":
    with open("test_file.txt", "r") as f:
        py_tokens = generate_tokens(f.readline)
        tokens = [convert_token(t) for t in py_tokens]
        # print(tokens))
        print(parse(g.del_stmt, tokens[:-1]))
        # print(tokens[2:7])
        print("DONE")