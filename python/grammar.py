from collections import deque

from derp.ast import iter_fields
from derp.grammar import Grammar
from derp.parsers import lit, star
from derp.utilities import unpack_n
from . import ast


# TODO parsing currently permits invalid assignments to literals. Should look into assignment contexts (or at least parsing the assignment node).

def emit_func_def(args):
    _, name, params, ret_type, _, body = unpack_n(args, 6)
    decorators = ()

    if ret_type == '':
        returns = None
    else:
        _, returns = ret_type

    if params == '':
        params = ast.arguments(args=(), vararg=None, kwonlyargs=(), kw_defaults=(), kwarg=None, defaults=())

    # Validate this here because incomplete parse branches might pass a partial argument list in this state this result
    # to the arg list reduction functions (where a syntax error might be uncalled for, and break the parse)
    if None in params.defaults:
        raise SyntaxError("Non-keyword arg after keyword(s)")

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
            defaults.append(None)  # So we can detect faulty args later
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


def emit_nl_indent_one_plus_dedent_suite(args):
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
        names, values = zip(*iter_fields(trailer))
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
    def_dict = dict(iter_fields(definition))
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


g = Grammar('Python')

g.single_input = lit('NEWLINE') | g.simple_stmt | g.compound_stmt & lit('NEWLINE')
# g.eval_input = g.test_list & +ter('NEWLINE') & ter('ENDMARKER')
g.file_input = (+(lit('NEWLINE') | g.stmt) & lit('ENDMARKER')) >> emit_file_input

g.decorator = (lit('@') & g.dotted_name & ~(lit('(') & ~g.arg_list & lit(')')) & lit('NEWLINE')) >> emit_decorator
g.decorators = star(g.decorator)

g.decorated = (g.decorators & (g.class_def | g.func_def)) >> emit_decorated  # Ignore async

g.func_def = (lit('def') & lit('ID') & g.parameters & ~(lit('->') & g.test) & lit(':') & g.suite) >> emit_func_def


def generate_args_list(tfpdef):
    tfpdef_opt_ass = tfpdef & ~(lit('=') & g.test)
    tfpdef_kwargs = lit('**') & tfpdef
    return ((tfpdef_opt_ass & +(lit(',') & tfpdef_opt_ass) & ~(lit(',') & ~(
        (lit('*') & ~tfpdef & +(lit(',') & tfpdef_opt_ass) & ~(
            lit(',') & tfpdef_kwargs)) | tfpdef_kwargs))) >> emit_first |
            (lit('*') & ~tfpdef & +(lit(',') & tfpdef_opt_ass) & ~(lit(',') & tfpdef_kwargs)) >> emit_varargs |
            tfpdef_kwargs >> emit_kwargs_only)


g.parameters = (lit('(') & ~g.typed_args_list & lit(')')) >> emit_params

g.typed_args_list = generate_args_list(g.tfpdef)
g.tfpdef = (lit('ID') & ~(lit(':') & g.test)) >> emit_tfpdef

g.var_args_list = generate_args_list(g.vfpdef)
g.vfpdef = lit('ID')

g.stmt = g.simple_stmt | g.compound_stmt

g.simple_stmt = (g.small_stmt & +(lit(';') & g.small_stmt) & ~lit(';') & lit(
    'NEWLINE')) >> emit_simple_stmt  # Single line multistmts emit tuple, others emit ast nodes
g.small_stmt = (
    g.expr_stmt | g.del_stmt | g.pass_stmt | g.flow_stmt | g.import_stmt | g.global_stmt | g.nonlocal_stmt | g.assert_stmt)
g.expr_stmt = (g.test_list_star_expr & g.augassign & (g.yield_expr | g.test_list)) >> emit_expr_augassign | \
              (g.test_list_star_expr & +(lit('=') & (g.yield_expr | g.test_list_star_expr))) >> emit_expr_assigns
g.test_list_star_expr = ((g.test | g.star_expr) & +(lit(',') & (g.test | g.star_expr)) & ~lit(
    ',')) >> emit_test_list_star_expr
g.augassign = lit('+=') | lit('-=') | lit('*=') | lit('/=') | lit('%=') | lit('&=') | lit('|=') | lit('^=') \
              | lit('<<=') | lit('>>=') | lit('**=') | lit('//=') | lit('@=')
g.del_stmt = (lit('del') & g.expr_list) >> emit_del
g.pass_stmt = lit('pass') >> emit_pass
g.flow_stmt = g.break_stmt | g.continue_stmt | g.return_stmt | g.raise_stmt | g.yield_stmt
g.break_stmt = lit('break') >> emit_break
g.continue_stmt = lit('continue') >> emit_continue
g.return_stmt = (lit('return') & ~g.test_list) >> emit_return
g.yield_stmt = g.yield_expr

g.raise_stmt = (lit('raise') & ~(g.test & ~(lit('from') & g.test))) >> emit_raise
g.import_stmt = g.import_name | g.import_from
g.import_name = (lit('import') & g.dotted_as_names) >> emit_import
g.import_from = (lit('from') &
                 ((+(lit('.') | lit('...')) & g.dotted_name) >> emit_import_from_dotted_name | star(
                     lit('.') | lit('...')) >> emit_import_from_no_name)
                 & lit('import') & (lit('*') >> emit_import_from_all | (
    lit('(') & g.import_as_names & lit(')')) >> emit_import_from_names_paren | g.import_as_names)) >> emit_import_from

# from & ((ALT & import)), aLT)
g.import_as_name = (lit('ID') & ~(lit('as') & lit('ID'))) >> emit_alias
g.import_as_names = (g.import_as_name & +(lit(',') & g.import_as_name) & ~lit(',')) >> emit_import_from_names
g.dotted_name = (lit('ID') & +(lit('.') & lit('ID'))) >> emit_dotted_name

g.dotted_as_name = (g.dotted_name & ~(lit('as') & lit('ID'))) >> emit_alias
g.dotted_as_names = (g.dotted_as_name & +(lit(',') & g.dotted_as_name)) >> emit_dotted_as_names
g.global_stmt = (lit('global') & lit('ID') & +(lit(',') & lit('ID'))) >> emit_global
g.nonlocal_stmt = (lit('nonlocal') & lit('ID') & +(lit(',') & lit('ID'))) >> emit_nonlocal
g.assert_stmt = (lit('assert') & g.test & ~(lit(',') & g.test)) >> emit_assert

g.compound_stmt = g.if_stmt | g.while_stmt | g.for_stmt | g.try_stmt | g.with_stmt | g.func_def | g.class_def | g.decorated
g.if_stmt = (lit('if') & g.test & lit(':') & g.suite & +(lit('elif') & g.test & lit(':') & g.suite) & ~(
    lit('else') & lit(':') & g.suite)) >> emit_if
g.while_stmt = (lit('while') & g.test & lit(':') & g.suite & ~(lit('else') & lit(':') & g.suite)) >> emit_while
g.for_stmt = (lit('for') & g.expr_list & lit('in') & g.test_list & lit(':') & g.suite & ~(
    lit('else') & lit(':') & g.suite)) >> emit_for
g.try_stmt = (lit('try') & lit(':') & g.suite &
              ((star(g.except_clause & lit(':') & g.suite) &
                ~(lit('else') & lit(':') & g.suite) &
                ~(lit('finally') & lit(':') & g.suite)) >> emit_try_except_else_finally |
               # Just finally no except
               (lit('finally') & lit(':') & g.suite) >> emit_try_finally
               )) >> emit_try
g.with_stmt = (lit('with') & g.with_item & +(lit(',') & g.with_item) & lit(':') & g.suite) >> emit_with

g.with_item = (g.test & ~(lit('as') & g.expr)) >> emit_alias
g.except_clause = lit('except') & ~((g.test & ~(lit('as') & lit('ID'))) >> emit_alias)

g.suite = g.simple_stmt >> emit_simple_stmt_suite | (lit('NEWLINE') & lit('INDENT') & star(g.stmt) & lit(
    'DEDENT')) >> emit_nl_indent_one_plus_dedent_suite  # Always emit flat tuple of nodes
g.test = (g.or_test & ~(lit('if') & g.or_test & lit('else') & g.test)) >> emit_test_left | g.lambda_def
g.test_no_cond = g.or_test | g.lambda_def_no_cond

g.lambda_def = (lit('lambda') & ~g.var_args_list & lit(':') & g.test) >> emit_lambda_def
g.lambda_def_no_cond = lit('lambda') & ~g.var_args_list & lit(':') & g.test_no_cond >> emit_lambda_def
g.or_test = (g.and_test & +(lit('or') & g.and_test)) >> emit_or_test
g.and_test = (g.not_test & +(lit('and') & g.not_test)) >> emit_and_test
g.not_test = (lit('not') & g.not_test) >> emit_not_test | g.comparison
g.comparison = (g.expr & +(g.comp_op & g.expr)) >> emit_comparison

g.comp_op = lit('<') | lit('>') | lit('==') | lit('>=') | lit('<=') | lit('<>') | lit('!=') | lit('in') | lit(
    'not') & lit('in') | lit('is') | lit('is') & lit('not')
g.star_expr = lit('*') & g.expr
g.expr = (g.xor_expr & +(lit('|') & g.xor_expr)) >> emit_expr

g.xor_expr = (g.and_expr & +(lit('^') & g.and_expr)) >> emit_xor_expr
g.and_expr = (g.shift_expr & +(lit('&') & g.shift_expr)) >> emit_and_expr
g.shift_expr = (g.arith_expr & +((lit('<<') | lit('>>')) & g.arith_expr)) >> emit_shift_expr
g.arith_expr = (g.term & +((lit('+') | lit('-')) & g.term)) >> emit_arith_exor
g.term = (g.factor & +((lit('*') | lit('@') | lit('/') | lit('%') | lit('//')) & g.factor)) >> emit_term
g.factor = ((lit('+') | lit('-') | lit('~')) & g.factor) >> emit_factor | g.power
g.power = (g.atom_expr & ~(lit('**') & g.factor)) >> emit_power

g.atom_expr = (g.atom & +g.trailer) >> emit_atom_expr
g.atom = ((lit('(') & ~(g.yield_expr | g.test_list_comp) & lit(')')) >> emit_generator_comp |
          (lit('[') & ~(g.yield_expr | g.test_list_comp) & lit(']')) >> emit_list_comp |
          (lit('{') & ~g.dict_or_set_maker & lit('}')) >> emit_dict_comp |
          lit('ID') >> emit_id | lit('NUMBER') >> emit_num | star(lit('LIT')) >> emit_lit |
          lit('...') >> emit_ellipsis | lit('None') >> emit_name_constant | lit('True') >> emit_name_constant |
          lit('False') >> emit_name_constant)

g.test_list_comp = ((g.test | g.star_expr) & (g.comp_for | (+(lit(',') & (g.test | g.star_expr)) & ~lit(','))
                                              >> emit_list_exprs)) >> emit_test_list_comp
g.trailer = (lit('(') & ~g.arg_list & lit(')')) >> emit_trailer_call | \
            (lit('[') & g.subscript_list & lit(']')) >> emit_trailer_subscript | \
            (lit('.') & lit('ID')) >> emit_trailer_attr
g.arg_list = (g.argument & +(lit(',') & g.argument) & ~lit(',')) >> emit_arg_list
g.subscript_list = (g.subscript & +(lit(',') & g.subscript) & ~lit(',')) >> emit_subscript_list

g.subscript = g.test | (~g.test & lit(':') & ~g.test & ~g.slice_op) >> emit_slice
g.slice_op = lit(':') & ~g.test
g.expr_list = ((g.expr | g.star_expr) & +(lit(',') & (g.expr | g.star_expr)) & ~lit(',')) >> emit_expr_list
g.test_list = (g.test & +(lit(',') & g.test) & ~lit(',')) >> emit_test_list

g.dict_or_set_maker = (
    (((g.test & lit(':') & g.test) >> emit_dict_pair | (lit('**') & g.expr) >> emit_dict_kwargs) & (g.comp_for | (
        +(lit(',') & ((g.test & lit(':') & g.test) >> emit_dict_pair | (lit('**') & g.expr) >> emit_dict_kwargs))
        & ~lit(',')))) >> emit_dict_maker | ((g.test | g.star_expr) &
                                             (g.comp_for | (+(lit(',') & (g.test | g.star_expr)) & ~lit(','))))
    >> emit_set_maker
)

g.argument = ((g.test & ~g.comp_for) >> emit_arg |
              (g.test & lit('=') & g.test) >> emit_keyword |
              (lit('**') & g.test) >> emit_kwargs |
              (lit('*') & g.test) >> emit_starred)
g.comp_iter = g.comp_for | g.comp_if

g.class_def = (lit('class') & lit('ID') & ~(lit('(') & ~g.arg_list & lit(')')) & lit(':') & g.suite) >> emit_class_def

g.comp_for = (lit('for') & g.expr_list & lit('in') & g.or_test & ~g.comp_iter) >> emit_comp_for
g.comp_if = (lit('if') & g.test_no_cond & ~g.comp_iter) >> emit_comp_if

g.yield_expr = (lit('yield') & ~g.yield_arg) >> emit_yield_expr
g.yield_arg = (lit('from') & g.test) | g.test_list

# Check all parsers were defined
g.ensure_parsers_defined()
