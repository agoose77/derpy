from collections import namedtuple
from tokenize import generate_tokens
import token
from keyword import iskeyword

from derp import parse, ter, epsilon, empty, Recurrence, BaseParser


Token = namedtuple("Token", "first second")


def convert_token(tok_info):
    if tok_info.type == token.NAME:
        value = tok_info.string
        if iskeyword(value):
            return Token(value, value)

        else:
            return Token('ID', tok_info.string)

    elif tok_info.type == token.STRING:
        return Token('LIT', tok_info.string)

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

    def __getattr__(self, name):
        result = Recurrence()
        self._recurrences[name] = result
        object.__setattr__(self, name, result) # To stop this being created again
        return result

    def __setattr__(self, name, value):
        assert isinstance(value, BaseParser), (name,value)
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


g = GrammarFactory()

def emit_program(args):
    raise NotImplementedError

file_input = (g.lines & ter('ENDMARKER')) >> emit_program

def emit_nl(args):
    print('A',args)
    return args

def emit_line(args):
    print('L', args)
    return args

g.lines = g.empty_line | (ter('NEWLINE') & g.lines) >> emit_nl | (g.stmt & g.lines) >> emit_line

def emit_func_def(args):
    pass
func_def = (ter('def') & ter('ID') & g.parameters & ter(':') & g.suite) >> emit_func_def

def emit_params(args):
    pass
g.parameters = (ter('(') & g.zero_plus_params & ter(')')) >> emit_params

def emit_param_list(args):
    pass

def emit_rest_of_params(args):
    pass
g.rest_of_ids = ~((ter(',') & ter('ID') & g.rest_of_ids) >> emit_rest_of_params)
g.zero_plus_params = (epsilon | (ter('ID') & g.rest_of_ids)>>emit_param_list | ter(','))


def emit_small_stmts(args):
    pass

more_small_stmts = (ter(';') & g.small_stmt & g.more_small_stmts) >> emit_small_stmts
zero_plus_small_stmts = +more_small_stmts
end_of_stmts = epsilon & ter('NEWLINE') | (ter(';') & ter('NEWLINE'))


g.stmt.parser = g.simple_stmt | g.compound_stmt
g.simple_stmt.parser = g.small_stmt & zero_plus_small_stmts & end_of_stmts


g.small_stmt.parser = g.expr_stmt | g.del_stmt | g.pass_stmt | g.flow_stmt | g.global_stmt | g.nonlocal_stmt | g.assert_stmt

augassign = ter('+=') | ter('-=') | ter('*=') | ter('/=') | ter('%=') | ter('&=') | ter('|=') | ter('^=') | ter('^=') \
            | ter('<<=') | ter('>>=') | ter('**=') | ter('//=')

def emit_aug_assign_stmt(args):
    pass
def emit_assign_stmt(args):
    pass
def emit_expr_stmt(args):
    pass
g.expr_stmt = (g.many_tests & augassign & g.many_tests) >> emit_aug_assign_stmt | \
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
return_expr = ~g.many_tests

def emit_from_stmt(args):
    return args
raise_from = ~((ter('from') & g.test) >> emit_from_stmt)

def emit_raise_new_exception(args):
    return args
raise_clause = ~((g.test & raise_from) >> emit_raise_new_exception)
g.return_stmt = ter('return') & return_expr >> emit_continue_stmt

def emit_raise_stmt(args):
    return args
g.raise_stmt = (ter('raise') & raise_clause) >> emit_raise_stmt

def emit_rest_of_ids(args):
    pass
g.zero_plus_ids = ~((ter(',') & ter('ID') & g.zero_plus_ids) >> emit_rest_of_ids)
g.global_stmt = (ter('global') & ter('ID') & g.zero_plus_ids) >> emit_global_stmt
g.nonlocal_stmt = (ter('nonlocal') & ter('ID') & g.zero_plus_ids) >> emit_nonlocal_stmt
zero_plus_tests = ~((ter(',') & g.test) >> emit_rest_of_tests)
g.assert_stmt = (ter('assert') & g.test & zero_plus_tests) >> emit_assert_stmt
g.compound_stmt = g.if_stmt | g.while_stmt | g.for_stmt | g.try_stmt | g.func_def

def emit_elifs(args):
    return args

zero_or_more_elifs = ~((ter('elif') & g.test & ter(':') & g.suite & g.zero_or_more_elifs) >> emit_elifs)
def emit_else_clause(args):
    pass

else_clause = ~((ter('else') & ter(':') & g.suite) >> emit_else_clause)
g.if_stmt = (ter('if') & g.test & ter(':') & g.suite & (zero_or_more_elifs & else_clause))

def emit_while_else_clause(args):
    return args
while_else_clause = ~((ter('else') & ter(':') & g.suite) >> emit_while_else_clause)

def emit_while_stmt(args):
    return args
g.while_stmt = (ter('while') & g.test & ter(':') & g.suite & while_else_clause) >> emit_while_stmt

def emit_for_else_clause(args):
    return args
for_else_clause = ~((ter('else') & ter(':') & g.sutie) >> emit_for_else_clause)
g.for_stmt = (ter('for') & ter('ID') & ter('in') & g.test & ter(':') & g.suite & for_else_clause) >> emit_for_stmt

def emit_finally_try_block(args):
    return args
finally_try_block = (ter('finally') & ter(':') & g.suite) >> emit_finally_try_block


def emit_except_vars(args):
    return args
except_vars = ~((ter('as') & ter('ID')) >> emit_except_vars)

def emit_except_type(args):
    return args
except_type = ~((g.test & except_vars) >> emit_except_type)
except_clause = (ter('except') & except_type)

def emit_except_else_clause(args):
    return args
except_else_clause = ~((ter('else') & ter(':') & g.suite) >> emit_except_else_clause)

def emit_finally_catch_block(args):
    return args
finally_catch_block = ~((ter('finally') & ter(':') & g.suite) >> emit_finally_catch_block)

else_block = except_else_clause >> emit_fail_if_not_parsed
finally_block = finally_catch_block >> emit_fail_if_not_parsed

g.zero_plus_excepts = ~((except_clause & ter(':') & g.suite & g.zero_plus_excepts) >> emit_except_clauses)

catch_and_finally_blocks = (except_clause & ter(':') & g.suite & g.zero_plus_excepts & else_block & finally_block) >> emit_except_else_finally

exception_handlers = catch_and_finally_blocks | finally_try_block
def emit_try_stmt(args):
    return args
g.try_stmt = (ter('try') & ter(':') & g.suite & exception_handlers) >> emit_try_stmt

def emit_stmts(args):
    return args

one_plus_stmts = (g.stmt & g.zero_plus_stmts) >> emit_stmts
g.zero_plus_stmts = ~one_plus_stmts

def emit_suite(args):
    return args
g.suite = g.simple_stmt | ((ter('NEWLINE') & ter('INDENT') & one_plus_stmts & ter('DEDENT')) >> emit_suite)

def emit_or_test(args):
    return args

comparison_operator = ter('<') | ter('>') | ter('==') | ter('>=') | ter('<=') | ter('<>') | ter('!=')

def emit_comparison_operator(args):
    return args
def emit_not_in(args):
    return args
def emit_is_not(args):
    return args
comparison_type = comparison_operator >> emit_comparison_operator | ter('in') | ter('is') |\
             (ter('not') & ter('in')) >> emit_not_in | (ter('is') & ter('not')) >> emit_is_not

def emit_comparison(args):
    return args
comparison = (g.star_expr & g.zero_plus_comps) >> emit_comparison

def emit_not_test(args):
    return args
g.not_test = (ter('not') & g.not_test) >> emit_not_test | comparison
g.zero_plus_nots = ~((ter('and') & g.not_test & g.zero_plus_nots))

def emit_and_test(args):
    return args
g.and_test = (g.not_test & g.zero_plus_nots) >> emit_and_test

def emit_zero_plus_ors(args):
    return args
g.zero_plus_ors = ~((ter('or') & g.and_test & g.zero_plus_ors) >> emit_zero_plus_ors)
g.or_test = (g.and_test & g.zero_plus_ors) >> emit_or_test
g.test = g.or_test | (g.or_test & ter('if') & g.or_test & ter('else') & g.test) >> emit_test | g.lambdaf

def emit_expr(args):
    return args
g.expr = (g.xor_expr & g.zero_plus_xors) >> emit_expr

def emit_star_expr(args):
    return args
g.star_expr = (~ter('*') & g.expr) == emit_star_expr

def emit_xor_expr(args):
    return args
g.xor_expr = (g.and_expr & g.zero_plus_ands) >> emit_xor_expr

g.zero_plus_xors =  ~

# Atom
atom = (g.tuple | g.dict | ter('ID') >> emit_id | ter('NUMBER') | g.string >> emit_string |
        ter('...') >> emit_dots | ter('None') | ter('True') | ter('False'))

# Tuple
def emit_tuple(args):
    pass
g.tuple = (ter('(') & ~g.test_or_tests & ter(')'))


#List
def emit_list(args):
    pass
g.list = (ter('[') & ~g.dict_or_set_maker & ter(']')) >> emit_list

# Dict
def emit_dict(args):
    pass
g.dict = (ter('{') & ~g.dict_or_set_maker & ter('}')) >> emit_dict


# String
def emit_string(args):
    pass
zero_plus_strs = Recurrence()
g.string = (ter('STRING') & zero_plus_strs) >> emit_string
zero_plus_strs = +g.string


if __name__ == "__main__":
    with open("test_file.txt", "r") as f:
        py_tokens = generate_tokens(f.readline)
        tokens = [convert_token(t) for t in py_tokens]

        print(parse(parser, tokens[:2]))

