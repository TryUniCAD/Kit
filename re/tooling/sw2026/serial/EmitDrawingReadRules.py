from __future__ import annotations

import argparse
from pprint import pformat

from DrawingReadRules import CLASS_SCHEMAS, compile_methods
from ReadRuleExpressions import constant, literal
from convert.adapters.solidworks.Archive.Header.HeaderClasses import KHeaderClasses


def reduce_expression(expression):
    action, *args = expression
    if action in {"literal", "scope", "context", "wire", "class_name"}:
        return expression
    if action == "sequence":
        return ("sequence", tuple(reduce_expression(item) for item in args[0]))
    if action == "mapping":
        return ("mapping", tuple((reduce_expression(key), reduce_expression(value)) for key, value in args[0]))
    if action == "compare":
        return constant(("compare", args[0], *(reduce_expression(item) for item in args[1:])))
    if action == "lookup_or" and args[0] == ("context",):
        key, default = args[1:]
        if key == literal("conditions"):
            return ("conditions",)
        return literal(1) if key == literal("owner_is_drawing") else reduce_expression(default)
    if action == "select":
        predicate, yes, no = (reduce_expression(item) for item in args)
        if predicate[0] == "literal":
            return yes if predicate[1] else no
        return "select", predicate, yes, no
    children = tuple(reduce_expression(item) for item in args)
    if action == "BitAnd" and children[0] == ("conditions",) and children[1][0] == "literal":
        if not children[1][1] & 0x40:
            return literal(0)
    return constant((action, *children))


def compact_expression(expression):
    action, *args = reduce_expression(expression)
    if action == "literal":
        return args[0]
    if (action, args[:1]) == ("lookup", [("scope",)]):
        return "field", compact_expression(args[1])
    if (action, args[:1]) == ("lookup_or", [("scope",)]):
        return "field", compact_expression(args[1]), compact_expression(args[2])
    if action == "compare":
        names, *values = args
        if len(names) != 1:
            raise ValueError("the qualified drawing context has no comparison chains")
        return names[0], *(compact_expression(value) for value in values)
    if action == "sequence":
        return "sequence", *(compact_expression(item) for item in args[0])
    if action == "mapping":
        if args != [()]:
            raise ValueError("the qualified drawing context uses only an empty map literal")
        return "empty_map",
    return action, *(compact_expression(item) for item in args)


def compact_rule(rule):
    kind, *args = rule
    if kind == "if":
        expression, yes, no = args
        predicate = compact_expression(expression)
        if not isinstance(predicate, tuple):
            return compact_rules(yes if predicate else no)
        return (("if", predicate, compact_rules(yes), compact_rules(no)),)
    if kind == "repeat":
        name, count, body = args
        return (("repeat", name, compact_expression(count), compact_rules(body)),)
    if kind in {"present", "counted", "condition", "if_virtual"}:
        return ((kind, *args[:-1], compact_rules(args[-1])),)
    if kind in {"fixed_bytes", "normalize"}:
        expression = compact_expression(args[-1])
        if kind == "fixed_bytes" and not isinstance(expression, int):
            return (("reject", "unqualified drawing data record"),)
        return ((kind, *args[:-1], expression),)
    if kind == "scalar":
        return ((args[1], args[0]),)
    return (rule,)


def compact_rules(rules):
    compact = []
    for rule in rules:
        for step in compact_rule(rule):
            merges = step[0] in {"u8", "i8", "u16", "i16", "u32", "i32", "u64", "i64", "f32", "f64", "text", "object"}
            if merges and compact and compact[-1][0] == step[0] and len(compact[-1][1]) + len(step[1]) < 45:
                prior, fields = compact.pop()
                compact.append((prior, f"{fields} {step[1]}"))
            else:
                compact.append(step)
    return tuple(compact)


def emit(which):
    classes = dict(sorted(CLASS_SCHEMAS.items()))
    header = dict(KHeaderClasses)
    rules = {
        method: compact_rules(steps)
        for method, steps in compile_methods().items()
        if (method, classes.get(method)) not in header or method in {"suObList", "su_CStringArray"}
    }
    declaration, rationale, table = {
        "grammar": ("KConceptShapes", "native concept schemas need a closed method grammar for this archive version", rules),
        "classes": ("KShapeClasses", "the drawing archive admits only the class schemas proved for this profile", classes),
    }[which]
    annotation = "Mapping[str, KRuleShape]" if which == "grammar" else "Mapping[str, int]"
    imports = ["from collections.abc import Mapping", "from types import MappingProxyType"]
    if which == "grammar":
        imports.extend(("", "from convert.adapters.solidworks.Drawing.Definition.ClauseTypes import KRuleShape"))
    return "\n".join((
        *imports, "",
        f"# {rationale}",
        f"{declaration}: {annotation} = MappingProxyType({pformat(table, width=86)})",
    )) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Emit the versioned, source-only SDK drawing read grammar")
    parser.add_argument("table", choices=("grammar", "classes"))
    print(emit(parser.parse_args().table), end="")
