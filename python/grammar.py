import token
import tokenize
from collections import deque
from io import StringIO
from keyword import iskeyword
from tokenize import generate_tokens

from derp import Token, ter, Recurrence, BaseParser, one_plus
from derp.utilities import unpack_n
from . import ast


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
        params = ast.arguments(args=(), vararg=None, kwonlyargs=(), kw_defaults=(), kwarg=None, defaults=())

    return ast.FunctionDef(name, params, body, decorators, returns)


def emit_params(args):
    _, typed_args, _ = unpack_n(args, 3)
    return typed_args


def emit_del(args):
    _, targets = args
    if isinstance(targets, ast.AST):
        targets = targets,
    return ast.Delete(targets)


def emit_break(args):
    return ast.Break()


def emit_pass(args):
    return ast.Pass()


def emit_continue(args):
    return ast.Continue()


def emit_import_from_dotted_name(args):
    many_dots, module = args
    level = sum(map(len, many_dots))
    return ast.importfrommodule(level, module)


def emit_import_from_no_name(args):
    dot_or_dots = args
    level = sum(map(len, dot_or_dots))
    return ast.importfrommodule(level, None)


def emit_import_from_all(args):
    asterisk, = args
    return ast.alias(asterisk)


def emit_import_from_names(args):
    alias, remainder, _ = unpack_n(args, 3)

    if remainder == '':
        aliases = alias,
    else:
        commas, following_aliases = zip(*remainder)
        aliases = (alias,) + following_aliases

    return ast.importfromsubmodules(aliases)


def emit_dotted_as_names(args):
    alias, remainder = unpack_n(args, 2)

    if remainder == '':
        aliases = alias,
    else:
        commas, following_aliases = zip(*remainder)
        aliases = (alias,) + following_aliases

    return aliases


def emit_import_from_names_paren(args):
    _, name_args, _ = unpack_n(args, 3)
    return name_args


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
    if test_list == '':
        return ast.Return(None)
    return ast.Return(test_list)


def emit_if(args):
    _, condition, _, body, elifs, else_ = unpack_n(args, 6)

    # Unpack the else statements
    if else_ == '':
        orelse = ()
    else:
        _, _, orelse = unpack_n(else_, 3)

    # Now deal with elifs
    if elifs != '':
        for elem in reversed(elifs):
            _, else_condition, _, else_body = unpack_n(elem, 4)
            orelse = ast.If(else_condition, else_body, orelse),

    return ast.If(condition, body, orelse)


def emit_while(args):
    _, condition, _, body, else_ = unpack_n(args, 5)
    if else_ == '':
        else_stmt = None
    else:
        else_stmt = else_
    return ast.While(condition, body, else_stmt)


def emit_for(args):
    _, target, _, iterable, _, body, optelse = unpack_n(args, 7)
    else_ = () if optelse == '' else optelse

    if isinstance(target, tuple):
        target = ast.Tuple(target)

    return ast.For(target, iterable, body, else_)


def emit_with(args):
    _, with_item, with_items, _, body = unpack_n(args, 5)
    if with_items == '':
        all_items = with_item,
    else:
        all_items = (with_item,) + with_items
    return ast.With(all_items, body)


def emit_with_item(args):
    test, opt_as = args
    if opt_as == "":
        return ast.alias(test, None)
    _, expr = opt_as
    return ast.alias(test, expr)


def emit_try_except_else_finally(args):
    excepts_and_bodies, opt_else_raw, opt_finally_raw = unpack_n(args, 3)

    except_handlers_list = []

    for element in excepts_and_bodies:
        clause, _, body = unpack_n(element, 3)
        _, opt_alias = clause

        type_ = None
        name = None
        if opt_alias != '':
            type_ = opt_alias.name
            name = opt_alias.asname

        except_handlers_list.append(ast.excepthandler(type_, name, body))

    except_handlers = tuple(except_handlers_list)

    if opt_else_raw == '':
        orelse = ()
    else:
        _, _, orelse = unpack_n(opt_else_raw, 3)

    if opt_finally_raw == '':
        finalbody = ()
    else:
        _, _, finalbody = unpack_n(opt_finally_raw, 3)

    return ast.tryexceptelsefinally(except_handlers, orelse, finalbody)


def emit_try_finally(args):
    _, _, body = unpack_n(args, 3)

    return ast.tryfinally(body)


def emit_try(args):
    _, _, body, following = unpack_n(args, 4)
    # Try = stmt.subclass('Try', 'body handlers orelse finalbody')
    if isinstance(following, ast.tryexceptelsefinally):
        return ast.Try(body, following.handlers, following.orelse, following.finalbody)
    return ast.Try(body, (), (), following.finalbody)


def emit_raise(args):
    _, opt_exc = args
    if opt_exc == '':
        return ast.Raise(None, None)

    exc, opt_cause = opt_exc
    if opt_cause == '':
        return ast.Raise(exc, None)
    _, cause = opt_cause
    return ast.Raise(exc, cause)


def emit_kwargs_only(kwarg):
    return ast.arguments((), None, (), (), kwarg, ())


def emit_tfpdef(args):
    arg_id, opt_annotation = args
    if opt_annotation != '':
        _, annotation = opt_annotation

    else:
        annotation = None

    return ast.arg(arg_id, annotation)


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

    return ast.arguments((), vararg, tuple(kw_only), tuple(kw_defaults), kwarg, ())


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

        elif defaults:
            defaults.append(None) # So we can detect faulty args later
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

    return ast.arguments(tuple(args), vararg, kwonlyargs, kw_defaults, kwarg, tuple(defaults))


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
    _, cond, _, orelse = unpack_n(opt_if, 4)
    return ast.IfExp(cond, or_test, orelse)


def emit_test_list_star_expr(args):
    test_or_star, opt_following_test_or_star, opt_trailing_comma = unpack_n(args, 3)
    if opt_following_test_or_star != '':
        _, exprs = zip(*opt_following_test_or_star)
        all_exprs = (test_or_star,) + exprs
        return ast.Tuple(all_exprs)
    return test_or_star


def emit_test_list(args):
    first, remainder, opt_trail = unpack_n(args, 3)
    if remainder == '':
        return first
    _, following = zip(*remainder)
    return ast.Tuple((first,) + following)


def emit_expr_augassign(args):
    test_list, augassign, yield_or_test_list = unpack_n(args, 3)
    if isinstance(test_list, ast.Tuple):
        raise SyntaxError("Invalid multiple assignments for augassign")

    lit_to_op = {'+=': ast.Add,
                 '-=': ast.Sub,
                 '*=': ast.Mult,
                 '/=': ast.Div,
                 '//=': ast.FloorDiv,
                 '@=': ast.MatMult,
                 '<<=': ast.LShift,
                 '>>=': ast.RShift,
                 '|=': ast.BitOr,
                 '&=': ast.BitAnd,
                 '^=': ast.BitXor,
                 '**=': ast.Pow,
                 '%=': ast.Mod}
    return ast.AugAssign(test_list, lit_to_op[augassign](), yield_or_test_list)


def emit_or_test(args):
    and_test, or_and_tests = args
    if or_and_tests == '':
        return and_test

    _, further_ands = zip(*or_and_tests)
    return ast.BoolOp(ast.Or(), (and_test,) + further_ands)


def emit_not_test(args):
    _, test = args
    return ast.UnaryOp(ast.Not(), test)


def emit_and_test(args):
    not_test, and_not_tests = args
    if and_not_tests == '':
        return not_test

    _, further_nots = zip(*and_not_tests)
    all_nots = (not_test,) + further_nots
    return ast.BoolOp(ast.And(), all_nots)


def emit_expr_assigns(args):
    test_list, assignments = args

    if assignments == '':
        return ast.Expr(test_list)

    if isinstance(test_list, ast.AST):
        test_list = test_list,

    _, (*exprs, value) = zip(*assignments)
    return ast.Assign(test_list + tuple(exprs), value)


def emit_comparison(args):
    expr, comp_exprs = args

    if comp_exprs == '':
        return expr

    op_table = {'==': ast.Eq, '!=': ast.NotEq, '>': ast.Gt,
                '<': ast.Lt, '>=': ast.GtE, '<=': ast.LtE,
                'is': ast.Is, ('is', 'not'): ast.IsNot,
                ('not', 'in'): ast.Gt, 'in': ast.In}
    ops, comparators = zip(*comp_exprs)
    op_enums = tuple(op_table[o]() for o in ops)
    return ast.Compare(expr, op_enums, comparators)


def emit_expr(args):
    xor, opt_xors = args
    if opt_xors == '':
        return xor
    left = xor
    for _, right in opt_xors:
        left = ast.BinOp(left, ast.BitOr(), right)
    return left


def emit_xor_expr(args):
    and_expr, opt_xor_exprs = args
    if opt_xor_exprs == '':
        return and_expr

    left = and_expr
    for _, right in opt_xor_exprs:
        left = ast.BinOp(left, ast.BitXOr(), right)
    return left


def emit_and_expr(args):
    shift_expr, opt_shift_exprs = args
    if opt_shift_exprs == '':
        return shift_expr
    left = shift_expr
    for _, right in opt_shift_exprs:
        left = ast.BinOp(left, ast.BitAnd(), right)
    return left


def emit_shift_expr(args):
    arith_expr, opt_shift_exprs = args
    if opt_shift_exprs == '':
        return arith_expr

    op_table = {'>>': ast.RShift, '<<': ast.LShift}

    left = arith_expr
    for shift_expr, right in opt_shift_exprs:
        left = ast.BinOp(left, op_table[shift_expr](), right)
    return left


def emit_arith_exor(args):
    term, opt_ariths = args
    if opt_ariths == '':
        return term

    op_table = {'+': ast.Add, '-': ast.Sub}

    left = term
    for arith_op, right in opt_ariths:
        left = ast.BinOp(left, op_table[arith_op](), right)
    return left


def emit_term(args):
    factor, opt_terms = args
    if opt_terms == '':
        return factor

    op_table = {'*': ast.Mult,
                '/': ast.Div,
                '%': ast.Mod,
                '//': ast.FloorDiv,
                '@': ast.MatMult}

    left = factor
    for term_op, right in opt_terms:
        left = ast.BinOp(left, op_table[term_op](), right)
    return left


def emit_factor(args):
    op, factor = args
    op_table = {'+': ast.UAdd, '-': ast.USub, '~': ast.Invert}
    return ast.UnaryOp(op_table[op](), factor)


def emit_power(args):
    atom, opt_factor = args
    if opt_factor == '':
        return atom
    _, exponent = opt_factor
    return ast.BinOp(atom, ast.Pow(), exponent)


def emit_id(value):
    return ast.Name(value)


def emit_arg_list(args):
    arg, opt_args, opt_comma = unpack_n(args, 3)
    if opt_args == '':
        return arg,
    commas, following_args = zip(*opt_args)
    return (arg,) + following_args


def emit_subscript_list(args):
    subscript, opt_subscripts, opt_comma = unpack_n(args, 3)
    if opt_subscripts == '':
        return subscript
    commas, following_subscripts = zip(*opt_subscripts)
    return ast.Tuple((subscript,) + following_subscripts)


def emit_kwargs(args):
    _, arg = args
    return ast.keyword(arg, None)


def emit_starred(args):
    _, arg = args
    return ast.Starred(arg)


def emit_nl_indented(args):
    _, _, list_of_stmts, _ = unpack_n(args, 4)
    stmts = []
    for n in list_of_stmts:
        if isinstance(n, ast.AST):
            stmts.append(n)
        else:
            stmts.extend(n)
    return tuple(stmts)


def emit_file_input(args):
    many_stmts, _ = args
    if many_stmts == '':
        return ()

    flattened_stmts = []
    for stmt_or_stmts in many_stmts:
        if stmt_or_stmts == "" or isinstance(stmt_or_stmts, ast.AST):  # TODO why is this never hit?
            flattened_stmts.append(stmt_or_stmts)
        else:
            flattened_stmts.extend(stmt_or_stmts)

    return ast.Module(tuple(flattened_stmts))


def split_args_list_to_arg_kwargs(arg_list):
    args = []
    keywords = []
    for arg in arg_list:
        if isinstance(arg, ast.keyword):
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
        bases, keywords = split_args_list_to_arg_kwargs(arg_list)
    return ast.ClassDef(cls_name, bases, keywords, body, ())


def emit_keyword(args):
    name, _, value = unpack_n(args, 3)
    if not isinstance(name, ast.Name):
        raise SyntaxError()
    return ast.keyword(name.id, value)


def emit_arg(args):
    name, opt_comp_for = args
    if opt_comp_for == '':
        return name

    return args


def emit_comp_for(args):
    _, expr_list, _, or_test, opt_if_or_for = unpack_n(args, 5)
    if opt_if_or_for == '':
        opt_if_or_for = None

    if isinstance(expr_list, tuple):
        expr_list = ast.Tuple(expr_list)

    return ast.compfor(expr_list, or_test, opt_if_or_for)


def emit_comp_if(args):
    _, cond, opt = unpack_n(args, 3)
    if opt == '':
        opt = None

    return ast.compif(cond, opt)


def emit_yield_expr(args):
    _, opt_arg = args
    if opt_arg == '':
        opt_arg = None
    return ast.Yield(opt_arg)


def emit_num(num):
    as_float = float(num)
    value = int(as_float) if as_float.is_integer() else as_float
    return ast.Num(value)


def emit_atom_expr(args):
    atom, trailers = args
    if trailers == '':
        return atom

    node = atom

    for trailer in trailers:
        names, values = zip(*ast.iter_fields(trailer))
        node = trailer.__class__(node, *values[1:])

    return node


def emit_expr_list(args):
    root_expr, opt_com_del_exprs, opt_trail = unpack_n(args, 3)
    if opt_com_del_exprs == '':
        return root_expr

    commas, exprs = zip(*opt_com_del_exprs)
    return (root_expr,) + exprs


def emit_lit(lits):
    first, *remainder = lits
    for lit in remainder:
        if not isinstance(lit, first.__class__):
            raise TypeError("Cannot concat str and bytes")

    value = first.__class__().join(lits)
    if isinstance(first, bytes):
        return ast.Bytes(value)
    return ast.Str(value)


def emit_list_comp(args):
    _, body, _ = unpack_n(args, 3)
    if body == '':
        return ast.List(())
    return body


def emit_generator_comp(args):
    _, body, _ = unpack_n(args, 3)
    if body == '':
        return ast.Tuple(())

    if isinstance(body, ast.Yield):
        return body

    if isinstance(body, ast.List):
        if len(body.elts) == 1:
            return body.elts[0]
        return ast.Tuple(body.elts)

    return ast.GeneratorExp(body.elt, body.generators)


def emit_trailer_call(args):
    _, body, _ = unpack_n(args, 3)
    if body == '':
        arguments, keywords = (), ()
    else:
        arguments, keywords = split_args_list_to_arg_kwargs(body)
    return ast.Call(None, arguments, keywords)


def emit_trailer_subscript(args):
    _, all_subscripts, _ = unpack_n(args, 3)
    return ast.Subscript(None, all_subscripts)


def emit_trailer_attr(args):
    _, ID = args
    return ast.Attribute(None, ID)


def comprehensions_from_compfor(compfor):
    comprehensions = deque()

    # Go from root to tail
    stack = deque()
    while compfor:
        stack.appendleft(compfor)
        compfor = compfor.for_or_if

    ifs = deque()

    # Iterate from tail
    for node in stack:
        if isinstance(node, ast.compif):
            ifs.appendleft(node.cond)

        else:
            assert isinstance(node, ast.compfor)
            comprehension = ast.comprehension(node.exprs, node.iterable, tuple(ifs))
            comprehensions.appendleft(comprehension)
            ifs.clear()

    return tuple(comprehensions)


def emit_set_maker(args):
    left, for_or_else = args
    if isinstance(for_or_else, ast.compfor):
        comprehensions = comprehensions_from_compfor(for_or_else)
        return ast.SetComp(left, comprehensions)

    # Unpack order is ((a,b), c) so in this branch the for_or_else is actually the comma
    expr_list, trailing_comma = for_or_else
    if expr_list != '':
        commas, exprs = zip(*expr_list)
    else:
        exprs = ()
    return ast.Set((left,) + exprs)


def emit_test_list_comp(args):
    test_or_stexpr, comp_for_or_list_of_comma_test_or_stexpr = args

    if isinstance(comp_for_or_list_of_comma_test_or_stexpr, ast.compfor):
        comprehensions = comprehensions_from_compfor(comp_for_or_list_of_comma_test_or_stexpr)
        return ast.ListComp(test_or_stexpr, comprehensions)

    else:
        exprs = (test_or_stexpr,) + comp_for_or_list_of_comma_test_or_stexpr
        return ast.List(exprs)


def emit_dict_comp(args):
    _, body, _ = unpack_n(args, 3)
    if body == '':
        return ast.Dict((), ())
    return body


def emit_list_exprs(args):
    list_exprs, opt_comma = args
    if list_exprs == '':
        return ()
    commas, exprs = zip(*list_exprs)
    return exprs


def emit_dict_pair(args):
    key, _, value = unpack_n(args, 3)
    return ast.keyword(key, value)


def emit_dict_kwargs(args):
    _, value = args
    return ast.keyword(None, value)


def emit_dict_maker(args):
    first, for_or_else = args

    if isinstance(for_or_else, ast.compfor):
        comprehensions = comprehensions_from_compfor(for_or_else)
        return ast.DictComp(first, comprehensions)

    # Unpack order is ((a,b), c) so in this branch the for_or_else is actually the comma
    expr_list, trailing_comma = for_or_else
    if expr_list != '':
        commas, exprs = zip(*expr_list)
    else:
        exprs = ()

    keys = [first.arg] + [e.arg for e in exprs]
    values = [first.value] + [e.value for e in exprs]

    return ast.Dict(tuple(keys), tuple(values))


def emit_name_constant(name):
    return ast.NameConstant(name)


def emit_ellipsis(_):
    return ast.Ellipsis_()


def emit_decorated(args):
    decorators, definition = args
    def_dict = dict(ast.iter_fields(definition))
    def_dict['decorator_list'] = decorators
    new_definition = definition.__class__(**def_dict)
    return new_definition


def emit_decorator(args):
    _, name_str, opt_calls, _ = unpack_n(args, 4)

    name = ast.Name(name_str)
    if opt_calls == '':
        return name

    _, arg_list, _ = unpack_n(opt_calls, 3)
    args, keywords = split_args_list_to_arg_kwargs(arg_list)
    return ast.Call(name, args, keywords)


def emit_dotted_name(args):
    first, remainder = args
    if remainder == '':
        return first

    return first + ''.join(s for p in remainder for s in p)


def emit_alias(args):
    name, opt_alias = args
    if opt_alias == '':
        return ast.alias(name, None)
    _, alias = opt_alias
    return ast.alias(name, alias)


def emit_slice(args):
    lower, _, upper, opt_slice_op = unpack_n(args, 4)
    if lower == '':
        lower = None

    if upper == '':
        upper = None

    step = None
    if opt_slice_op != '':
        _, _test3 = opt_slice_op
        if _test3 != '':
            step = _test3

    return ast.Slice(lower, upper, step)


def emit_simple_stmt_suite(stmt_or_stmts):
    if isinstance(stmt_or_stmts, ast.AST):
        return stmt_or_stmts,
    return stmt_or_stmts


g = GrammarFactory()

g.single_input = (ter('NEWLINE') | g.simple_stmt | g.compound_stmt) & ter('NEWLINE')
# g.eval_input = g.test_list & +ter('NEWLINE') & ter('ENDMARKER')
g.file_input = (+(ter('NEWLINE') | g.stmt) & ter('ENDMARKER')) >> emit_file_input

g.decorator = (ter('@') & g.dotted_name & ~(ter('(') & ~g.arg_list & ter(')')) & ter('NEWLINE')) >> emit_decorator
g.decorators = one_plus(g.decorator)

g.decorated = (g.decorators & (g.class_def | g.func_def)) >> emit_decorated  # Ignore async

g.func_def = (ter('def') & ter('ID') & g.parameters & ~(ter('->') & g.test) & ter(':') & g.suite) >> emit_func_def


def generate_args_list(tfpdef):
    tfpdef_opt_ass = tfpdef & ~(ter('=') & g.test)
    tfpdef_kwargs = ter('**') & tfpdef
    return ((tfpdef_opt_ass & +(ter(',') & tfpdef_opt_ass) & ~(ter(',') & ~(
            (ter('*') & ~tfpdef & +(ter(',') & tfpdef_opt_ass) & ~(
            ter(',') & tfpdef_kwargs)) | tfpdef_kwargs))) >> emit_first |
            (ter('*') & ~tfpdef & +(ter(',') & tfpdef_opt_ass) & ~(ter(',') & tfpdef_kwargs)) >> emit_varargs |
            tfpdef_kwargs >> emit_kwargs_only)


g.parameters = (ter('(') & ~g.typed_args_list & ter(')')) >> emit_params

g.typed_args_list = generate_args_list(g.tfpdef)
g.tfpdef = (ter('ID') & ~(ter(':') & g.test)) >> emit_tfpdef

g.var_args_list = generate_args_list(g.vfpdef)
g.vfpdef = ter('ID')

g.stmt = g.simple_stmt | g.compound_stmt

g.simple_stmt = (g.small_stmt & +(ter(';') & g.small_stmt) & ~ter(';') & ter(
    'NEWLINE')) >> emit_simple_stmt  # Single line multistmts emit tuple, others emit ast nodes
g.small_stmt = (
    g.expr_stmt | g.del_stmt | g.pass_stmt | g.flow_stmt | g.import_stmt | g.global_stmt | g.nonlocal_stmt | g.assert_stmt)
g.expr_stmt = (g.test_list_star_expr & g.augassign & (g.yield_expr | g.test_list)) >> emit_expr_augassign | \
              (g.test_list_star_expr & +(ter('=') & (g.yield_expr | g.test_list_star_expr))) >> emit_expr_assigns
g.test_list_star_expr = ((g.test | g.star_expr) & +(ter(',') & (g.test | g.star_expr)) & ~ter(
    ',')) >> emit_test_list_star_expr
g.augassign = ter('+=') | ter('-=') | ter('*=') | ter('/=') | ter('%=') | ter('&=') | ter('|=') | ter('^=') \
              | ter('<<=') | ter('>>=') | ter('**=') | ter('//=') | ter('@=')
g.del_stmt = (ter('del') & g.expr_list) >> emit_del
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
                 ((+(ter('.') | ter('...')) & g.dotted_name) >> emit_import_from_dotted_name | one_plus(
                     ter('.') | ter('...')) >> emit_import_from_no_name)
                 & ter('import') & (ter('*') >> emit_import_from_all | (
    ter('(') & g.import_as_names & ter(')')) >> emit_import_from_names_paren | g.import_as_names)) >> emit_import_from
g.import_as_name = (ter('ID') & ~(ter('as') & ter('ID'))) >> emit_alias
g.import_as_names = (g.import_as_name & +(ter(',') & g.import_as_name) & ~ter(',')) >> emit_import_from_names
g.dotted_name = (ter('ID') & +(ter('.') & ter('ID'))) >> emit_dotted_name

g.dotted_as_name = (g.dotted_name & ~(ter('as') & ter('ID'))) >> emit_alias
g.dotted_as_names = (g.dotted_as_name & +(ter(',') & g.dotted_as_name)) >> emit_dotted_as_names
g.global_stmt = (ter('global') & ter('ID') & +(ter(',') & ter('ID'))) >> emit_global
g.nonlocal_stmt = (ter('nonlocal') & ter('ID') & +(ter(',') & ter('ID'))) >> emit_nonlocal
g.assert_stmt = (ter('assert') & g.test & ~(ter(',') & g.test)) >> emit_assert

g.compound_stmt = g.if_stmt | g.while_stmt | g.for_stmt | g.try_stmt | g.with_stmt | g.func_def | g.class_def | g.decorated
g.if_stmt = (ter('if') & g.test & ter(':') & g.suite & +(ter('elif') & g.test & ter(':') & g.suite) & ~(
    ter('else') & ter(':') & g.suite)) >> emit_if
g.while_stmt = (ter('while') & g.test & ter(':') & g.suite & ~(ter('else') & ter(':') & g.suite)) >> emit_while
g.for_stmt = (ter('for') & g.expr_list & ter('in') & g.test_list & ter(':') & g.suite & ~(
    ter('else') & ter(':') & g.suite)) >> emit_for
g.try_stmt = (ter('try') & ter(':') & g.suite &
              ((one_plus(g.except_clause & ter(':') & g.suite) &
                ~(ter('else') & ter(':') & g.suite) &
                ~(ter('finally') & ter(':') & g.suite)) >> emit_try_except_else_finally |
               # Just finally no except
               (ter('finally') & ter(':') & g.suite) >> emit_try_finally
               )) >> emit_try
g.with_stmt = (ter('with') & g.with_item & +(ter(',') & g.with_item) & ter(':') & g.suite) >> emit_with

g.with_item = (g.test & ~(ter('as') & g.expr)) >> emit_alias
g.except_clause = ter('except') & ~((g.test & ~(ter('as') & ter('ID'))) >> emit_alias)

g.suite = g.simple_stmt >> emit_simple_stmt_suite | (ter('NEWLINE') & ter('INDENT') & one_plus(g.stmt) & ter(
    'DEDENT')) >> emit_nl_indented  # Always emit flat tuple of nodes
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

g.atom_expr = (g.atom & +g.trailer) >> emit_atom_expr
g.atom = ((ter('(') & ~(g.yield_expr | g.test_list_comp) & ter(')')) >> emit_generator_comp |
          (ter('[') & ~(g.yield_expr | g.test_list_comp) & ter(']')) >> emit_list_comp |
          (ter('{') & ~g.dict_or_set_maker & ter('}')) >> emit_dict_comp |
          ter('ID') >> emit_id | ter('NUMBER') >> emit_num | one_plus(ter('LIT')) >> emit_lit | ter('...') >> emit_ellipsis |
          ter('None') >> emit_name_constant | ter('True') >> emit_name_constant | ter('False') >> emit_name_constant)

g.test_list_comp = ((g.test | g.star_expr) & (
    g.comp_for | (+(ter(',') & (g.test | g.star_expr)) & ~ter(',')) >> emit_list_exprs)) >> emit_test_list_comp
g.trailer = (ter('(') & ~g.arg_list & ter(')')) >> emit_trailer_call | \
            (ter('[') & g.subscript_list & ter(']')) >> emit_trailer_subscript | \
            (ter('.') & ter('ID')) >> emit_trailer_attr
g.arg_list = (g.argument & +(ter(',') & g.argument) & ~ter(',')) >> emit_arg_list
g.subscript_list = (g.subscript & +(ter(',') & g.subscript) & ~ter(',')) >> emit_subscript_list

g.subscript = g.test | (~g.test & ter(':') & ~g.test & ~g.slice_op) >> emit_slice
g.slice_op = ter(':') & ~g.test
g.expr_list = ((g.expr | g.star_expr) & +(ter(',') & (g.expr | g.star_expr)) & ~ter(',')) >> emit_expr_list
g.test_list = (g.test & +(ter(',') & g.test) & ~ter(',')) >> emit_test_list

g.dict_or_set_maker = (
    (((g.test & ter(':') & g.test) >> emit_dict_pair | (ter('**') & g.expr) >> emit_dict_kwargs) & (g.comp_for | (
    +(ter(',') & ((g.test & ter(':') & g.test) >> emit_dict_pair | (ter('**') & g.expr) >> emit_dict_kwargs))
    & ~ter(',')))) >> emit_dict_maker | ((g.test | g.star_expr) &
                                         (g.comp_for | (+(ter(',') & (g.test | g.star_expr)) & ~ter(',')))) >> emit_set_maker
)

g.argument = ((g.test & ~g.comp_for) >> emit_arg |
              (g.test & ter('=') & g.test) >> emit_keyword |
              (ter('**') & g.test) >> emit_kwargs |
              (ter('*') & g.test) >> emit_starred)
g.comp_iter = g.comp_for | g.comp_if

g.class_def = (ter('class') & ter('ID') & ~(ter('(') & ~g.arg_list & ter(')')) & ter(':') & g.suite) >> emit_class_def

g.comp_for = (ter('for') & g.expr_list & ter('in') & g.or_test & ~g.comp_iter) >> emit_comp_for
g.comp_if = (ter('if') & g.test_no_cond & ~g.comp_iter) >> emit_comp_if

g.yield_expr = (ter('yield') & ~g.yield_arg) >> emit_yield_expr
g.yield_arg = (ter('from') & g.test) | g.test_list

# Check all parsers were defined
g.ensure_parsers_defined()
