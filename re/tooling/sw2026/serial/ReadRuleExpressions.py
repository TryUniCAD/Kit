from __future__ import annotations

import ast
import dis
import inspect
import operator
from functools import lru_cache
from pathlib import Path

from Dsl import ver


class UnportableExpression(ValueError):
    pass


@lru_cache(maxsize=None)
def source_tree(filename):
    return ast.parse(Path(filename).read_text(), filename)


def within(position, node):
    return (node.lineno, node.col_offset) <= position <= (node.end_lineno, node.end_col_offset)


def callable_source(function):
    code = function.__code__
    tree = source_tree(code.co_filename)
    if code.co_name == "<lambda>":
        options = [node for node in ast.walk(tree) if isinstance(node, ast.Lambda) and node.lineno == code.co_firstlineno]
        if len(options) == 1:
            return options[0].body
        positions = [
            (item.positions.lineno, item.positions.col_offset)
            for item in dis.get_instructions(function)
            if item.opname not in {"RESUME", "COPY_FREE_VARS"} and item.positions and item.positions.lineno is not None and item.positions.col_offset is not None
        ]
        candidates = [node.body for node in options if all(within(point, node.body) for point in positions)]
        if len(candidates) == 1:
            return candidates[0]
    else:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == code.co_name and node.lineno == code.co_firstlineno:
                return node.body
    raise UnportableExpression(f"cannot resolve format predicate {function.__qualname__}")


def literal(value):
    if value is None or type(value) in (int, float, str, bool):
        return ("literal", value)
    if isinstance(value, (set, frozenset)):
        value = sorted(value)
    if isinstance(value, (tuple, list)):
        return ("sequence", tuple(literal(item) for item in value))
    if isinstance(value, dict):
        return ("mapping", tuple((literal(key), literal(item)) for key, item in value.items()))
    raise UnportableExpression(f"unsupported predicate constant type {type(value).__name__}")


def compile_callable(function, arguments, version):
    if function is ver:
        return literal(version)
    if function.__module__ == "defs.ResolvedCore" and function.__name__ == "isa":
        from defs.ResolvedCore import PARENT, isa

        value, target = arguments
        if target[0] == "literal":
            names = sorted(name for name in PARENT.keys() | {target[1]} if isa(name, target[1]))
            return ("compare", ("In",), value, literal(names))
    code = function.__code__
    if code.co_argcount != len(arguments):
        raise UnportableExpression(f"invalid predicate argument count for {function.__qualname__}")
    closure = inspect.getclosurevars(function)
    environment = {**closure.globals, **closure.nonlocals, **closure.builtins}
    bindings = dict(zip(code.co_varnames, arguments))
    body = callable_source(function)
    if isinstance(body, list):
        return compile_body(body, bindings, environment, version)
    return compile_expr(body, bindings, environment, version)


def compile_body(body, bindings, environment, version):
    bindings = dict(bindings)
    for index, step in enumerate(body):
        if isinstance(step, ast.Assign) and len(step.targets) == 1 and isinstance(step.targets[0], ast.Name):
            bindings[step.targets[0].id] = compile_expr(step.value, bindings, environment, version)
        elif isinstance(step, ast.Return):
            return compile_expr(step.value, bindings, environment, version)
        elif isinstance(step, ast.If):
            condition = compile_expr(step.test, bindings, environment, version)
            left = compile_body([*step.body, *body[index + 1 :]], bindings, environment, version)
            right = compile_body([*step.orelse, *body[index + 1 :]], bindings, environment, version)
            return ("select", condition, left, right)
        else:
            raise UnportableExpression(f"unsupported predicate statement {type(step).__name__}")
    raise UnportableExpression("format predicate has no return value")


def compile_expr(node, bindings, environment, version):
    def child(value):
        return compile_expr(value, bindings, environment, version)

    if isinstance(node, ast.Constant):
        return literal(node.value)
    if isinstance(node, ast.Name):
        if node.id in bindings:
            return bindings[node.id]
        if node.id in environment:
            return literal(environment[node.id])
        raise UnportableExpression(f"unknown format predicate name {node.id}")
    if isinstance(node, ast.Attribute):
        owner = child(node.value)
        member = (owner, node.attr)
        if member == (("node",), "cls"):
            return ("class_name",)
        if member == (("archive",), "ctx"):
            return ("context",)
        if member == (("archive",), "version"):
            return literal(version)
        if member == (("archive",), "base"):
            return literal(1)
        raise UnportableExpression(f"unsupported predicate attribute {node.attr}")
    if isinstance(node, ast.Call):
        if node.keywords:
            raise UnportableExpression("format predicate has unsupported keyword arguments")
        arguments = tuple(child(value) for value in node.args)
        if isinstance(node.func, ast.Attribute) and node.func.attr == "get":
            default = arguments[1] if len(arguments) == 2 else literal(None)
            return ("lookup_or", child(node.func.value), arguments[0], default)
        if isinstance(node.func, ast.Name):
            function = environment.get(node.func.id)
            if function in (max, min, int, bool, len):
                return (function.__name__, *arguments)
            if inspect.isfunction(function):
                return compile_callable(function, arguments, version)
        raise UnportableExpression("unsupported function in format predicate")
    if isinstance(node, ast.Subscript):
        return ("lookup", child(node.value), child(node.slice))
    if isinstance(node, ast.BinOp):
        return (type(node.op).__name__, child(node.left), child(node.right))
    if isinstance(node, ast.UnaryOp):
        return (type(node.op).__name__, child(node.operand))
    if isinstance(node, ast.BoolOp):
        return (type(node.op).__name__, *(child(value) for value in node.values))
    if isinstance(node, ast.Compare):
        return ("compare", tuple(type(op).__name__ for op in node.ops), child(node.left), *(child(value) for value in node.comparators))
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return ("sequence", tuple(child(value) for value in node.elts))
    if isinstance(node, ast.Dict) and all(key is not None for key in node.keys):
        return ("mapping", tuple((child(key), child(value)) for key, value in zip(node.keys, node.values, strict=True)))
    if isinstance(node, ast.IfExp):
        return ("select", child(node.test), child(node.body), child(node.orelse))
    raise UnportableExpression(f"unsupported predicate expression {type(node).__name__}")


COMPARE = {
    "Eq": operator.eq, "NotEq": operator.ne, "Lt": operator.lt, "LtE": operator.le,
    "Gt": operator.gt, "GtE": operator.ge, "Is": operator.is_, "IsNot": operator.is_not,
    "In": lambda left, right: left in right, "NotIn": lambda left, right: left not in right,
}
OPERATORS = {
    "Add": operator.add, "Sub": operator.sub, "Mult": operator.mul, "FloorDiv": operator.floordiv,
    "BitAnd": operator.and_, "BitOr": operator.or_, "BitXor": operator.xor, "LShift": operator.lshift,
    "RShift": operator.rshift, "USub": operator.neg, "UAdd": operator.pos, "Invert": operator.invert,
    "Not": operator.not_, "bool": bool, "int": int, "len": len, "max": max, "min": min,
}


def evaluate(expression, variables):
    action, *args = expression
    if action == "literal":
        return args[0]
    if action in variables:
        return variables[action]
    if action == "sequence":
        return tuple(evaluate(child, variables) for child in args[0])
    if action == "mapping":
        return {evaluate(key, variables): evaluate(child, variables) for key, child in args[0]}
    if action == "lookup":
        owner, key = (evaluate(child, variables) for child in args)
        return owner[key]
    if action == "lookup_or":
        owner, key, default = (evaluate(child, variables) for child in args)
        return owner.get(key, default)
    if action == "select":
        condition, when_true, when_false = args
        return evaluate(when_true if evaluate(condition, variables) else when_false, variables)
    if action in {"And", "Or"}:
        for child in args:
            result = evaluate(child, variables)
            if bool(result) == (action == "Or"):
                return result
        return result
    if action == "compare":
        names, first, *rest = args
        left = evaluate(first, variables)
        for name, right_rule in zip(names, rest, strict=True):
            right = evaluate(right_rule, variables)
            if not COMPARE[name](left, right):
                return False
            left = right
        return True
    if action in OPERATORS:
        return OPERATORS[action](*(evaluate(child, variables) for child in args))
    raise UnportableExpression(f"unknown format expression action {action}")


def constant(expression):
    try:
        return literal(evaluate(expression, {}))
    except UnportableExpression:
        return expression
