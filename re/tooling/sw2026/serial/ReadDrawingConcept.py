from __future__ import annotations

import struct
from collections import Counter

from DrawingReadRules import CLASS_SCHEMAS, VERSION
from ReadRuleExpressions import evaluate
from Schema import Scope
from defs.Drawing import DRAWING_CLSID

from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Reading.ReadNativeCount import ReadCountMut
from convert.adapters.solidworks.Archive.Reading.ReadNativeText import ReadTextMut
from convert.adapters.solidworks.Archive.Reading.ReadTypedNode import ReadTypedMut


SCALARS = {kind: struct.Struct(code) for kind, code in {
    "u8": "<B", "i8": "<b", "u16": "<H", "i16": "<h", "u32": "<I", "i32": "<i",
    "u64": "<Q", "i64": "<q", "f32": "<f", "f64": "<d",
}.items()}


def scalar(cursor, kind):
    rule = SCALARS[kind]
    return rule.unpack(cursor.TakeBytes(rule.size))[0]


class ConceptReader:
    def __init__(self, data, version, rules):
        if version != VERSION:
            raise ValueError(f"unsupported drawing concept version {version}")
        self.reader = GraphReader(BinaryReader(data), ArchiveMaps(1), self.read_object)
        self.rules = rules
        self.context = {"owner_is_drawing": 1}
        self.calls = Counter()
        self.methods = []

    def root(self):
        cursor = self.reader.Cursor
        for _ in range(5):
            scalar(cursor, "i32")
        clsid = scalar(cursor, "u32"), scalar(cursor, "u16"), scalar(cursor, "u16"), cursor.TakeBytes(8)
        if clsid != DRAWING_CLSID:
            raise ValueError("invalid drawing concept document CLSID")
        return ReadTypedMut(self.reader, "moDrawing_c")

    def read_object(self, reader, owner):
        descriptor = owner.ClassValue
        if not isinstance(descriptor, RuntimeClass) or CLASS_SCHEMAS.get(descriptor.NameValue) != descriptor.SchemaValue:
            raise ValueError(f"unsupported drawing class {descriptor}")
        self.method(descriptor.NameValue, Scope({}, None, owner.FieldsValue), descriptor.NameValue)

    def method(self, name, scope, owner):
        if name not in self.rules:
            raise ValueError(f"unqualified drawing read method {name}")
        if len(self.methods) >= 60:
            raise ValueError("drawing concept nesting exceeds the supported depth")
        self.methods.append(name)
        self.calls[name] += 1
        try:
            self.read_rules(self.rules[name], scope, owner)
        finally:
            self.methods.pop()

    def read_rules(self, rules, scope, owner):
        cursor = self.reader.Cursor
        variables = {"scope": scope, "context": self.context, "class_name": owner}
        for kind, *arguments in rules:
            match kind, arguments:
                case "scalar", [name, code]:
                    scope[name] = scalar(cursor, code)
                case "text", [name]:
                    scope[name] = ReadTextMut(cursor)
                case "count", [name]:
                    scope[name] = ReadCountMut(cursor, 1)
                case "object", [name]:
                    scope[name] = ReadNodeMut(self.reader)
                case "inline_header", [] if owner == "moDrawing_c":
                    scope["fa8"] = ReadTypedMut(self.reader, "moHeader_c")
                case "fixed_bytes", [name, width]:
                    scope[name] = cursor.TakeBytes(evaluate(width, variables))
                case "base", [method]:
                    self.method(method, scope, owner)
                case "embedded", [name, method]:
                    item = Scope(scope, None)
                    self.method(method, item, owner)
                    scope[name] = item.own
                case "if", [predicate, yes, no]:
                    self.read_rules(yes if evaluate(predicate, variables) else no, scope, owner)
                case "virtual", [rows]:
                    target = dict(rows)[owner]
                    if target is not None:
                        self.method(target, scope, owner)
                case "if_virtual", [expected, enabled, body] if owner in expected:
                    if owner in enabled:
                        self.read_rules(body, scope, owner)
                case "repeat", [name, count_rule, body]:
                    scope[name] = self.repeat(body, evaluate(count_rule, variables), scope, owner)
                case "counted", [name, code, body]:
                    count = scalar(cursor, code)
                    scope[name + "#count"] = count
                    scope[name] = self.repeat(body, max(count, 0), scope, owner)
                case "present", [flag, code, body]:
                    scope[flag] = scalar(cursor, code)
                    if scope[flag]:
                        self.read_rules(body, scope, owner)
                case "normalize", [name, code, expression]:
                    value = scalar(cursor, code)
                    scope[name + "#wire"] = value
                    scope[name] = evaluate(expression, {**variables, "wire": value})
                case "condition", [mask, body]:
                    saved = self.context.get("conditions", 0)
                    self.context["conditions"] = saved | mask
                    try:
                        self.read_rules(body, scope, owner)
                    finally:
                        self.context["conditions"] = saved
                case "exclude_conditions", [mask] if not self.context.get("conditions", 0) & mask:
                    continue
                case "reject", [reason]:
                    raise ValueError(f"unqualified drawing branch in {self.methods[-1]}: {reason}")
                case _:
                    raise ValueError(f"unsupported drawing member in {self.methods[-1]}: {kind}")

    def repeat(self, rules, count, parent, owner):
        remaining = self.reader.Cursor.GetRemaining()
        if type(count) is not int or not 0 <= count <= remaining:
            raise ValueError("drawing collection count exceeds the remaining stream")
        items = []
        for index in range(count):
            item = Scope(parent, index)
            start = self.reader.Cursor.GetOffset()
            self.read_rules(rules, item, owner)
            if start == self.reader.Cursor.GetOffset():
                raise ValueError("drawing collection entry consumed no archive data")
            items.append(item.own)
        return items
