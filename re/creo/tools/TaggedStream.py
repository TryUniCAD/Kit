"""Research-only tagged-stream parser for Creo PSB sections.

The grammar is the one recorded in `re/creo/data-model/DataModel.md` and confirmed
against the `ugc_read_structure` and `ugc_ieee_unformat_double` decompilations in
`re/creo/loader/Loader.md`. This module is not production code; it exists to
validate the field map against the empty control and the one-feature ladder.

The stream is a flat token sequence. `e0 <type> <name> 00` defines a field and
adds it to the global field table. The field value follows, but it may be
preceded by `f1`-`f4` close tokens that pop structure levels first. `f7 <id>`
selects the id-th field of the global field table, so a later record can reuse
the first record's schema without redefining it. After a value, the field index
advances, so the fields after an `f7` selection are read positionally.

Array counts and body dimensions are part of the field definition: the first
record emits `f8 <count>` or `f9 <rows> <cols>`, and later records reuse the
stored count.
"""

from __future__ import annotations

import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path


KOneByteDouble = {
    0x0F: 0.0,
    0x18: 1.0,
}


@dataclass
class FieldDef:
    name: str
    type_id: int
    count: int | None = None


@dataclass
class Node:
    name: str
    type_id: int
    value: object = None
    children: list["Node"] = field(default_factory=list)


class Reader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def byte(self) -> int:
        value = self.data[self.pos]
        self.pos += 1
        return value

    def take(self, count: int) -> bytes:
        value = self.data[self.pos : self.pos + count]
        self.pos += count
        return value

    def cstring(self) -> str:
        end = self.data.find(b"\x00", self.pos)
        if end < 0:
            end = len(self.data)
        value = self.data[self.pos : end].decode("latin-1")
        self.pos = end + 1
        return value

    def compact_int(self) -> int:
        first = self.byte()
        if first <= 0x7F:
            return first
        if first <= 0xBF:
            return ((first & 0x3F) << 8) | self.byte()
        if first <= 0xDF:
            return ((first & 0x1F) << 16) | (self.byte() << 8) | self.byte()
        if first == 0xF5:
            return -self.compact_int()
        if first == 0xF6:
            return -1
        if 0xE8 <= first <= 0xEB:
            count = first - 0xE7
            return int.from_bytes(self.take(count), "big")
        raise ValueError(f"unknown compact integer prefix {first:#04x} at {self.pos - 1:#x}")


def UnformatDouble(text: str) -> float:
    if not text:
        return 0.0
    if text[0] == "R":
        raw = bytes.fromhex(text[1:])
        return struct.unpack(">d", raw[:8].ljust(8, b"\x00"))[0]
    raw = bytes.fromhex(text)
    return struct.unpack(">d", raw[:8].ljust(8, b"\x00"))[0]


class Parser:
    def __init__(self, data: bytes) -> None:
        self.reader = Reader(data)
        self.nodes: list[Node] = []
        self.fields: list[FieldDef] = []
        self.index = 0
        self.stack: list[list[int]] = [[]]
        self.feature_start = 0

    def ReadDouble(self) -> float:
        reader = self.reader
        first = reader.data[reader.pos]
        if first in KOneByteDouble:
            reader.pos += 1
            return KOneByteDouble[first]
        if first == 0x52:
            reader.pos += 1
            return struct.unpack(">d", reader.take(8))[0]
        start = reader.pos
        while reader.pos < len(reader.data) and chr(reader.data[reader.pos]) in "0123456789abcdefABCDEF":
            reader.pos += 1
        text = reader.data[start : reader.pos].decode("latin-1")
        if not text:
            raise ValueError(f"double expected at {start:#x}")
        return UnformatDouble(text)

    def ReadScalar(self, type_id: int) -> object:
        reader = self.reader
        if type_id in (0x01, 0x05, 0x07, 0x08, 0x09, 0x0B):
            return reader.compact_int()
        if type_id == 0x02:
            return self.ReadDouble()
        if type_id in (0x03, 0x0A):
            return reader.cstring()
        if type_id == 0x04:
            return reader.byte()
        if type_id == 0x06:
            return struct.unpack(">f", reader.take(4))[0]
        raise ValueError(f"unknown field type {type_id:#04x} at {reader.pos:#x}")

    def ReadArray(self, type_id: int, count: int | None) -> list[object]:
        reader = self.reader
        values: list[object] = []
        while reader.pos < len(reader.data):
            if count is not None and len(values) >= count:
                if reader.pos < len(reader.data) and reader.data[reader.pos] == 0xFB:
                    reader.pos += 1
                break
            token = reader.data[reader.pos]
            if token == 0xE7:
                reader.pos += 1
                repeat = reader.compact_int()
                if not values:
                    raise ValueError("repeat without a previous value")
                values.extend([values[-1]] * repeat)
                continue
            if 0xE4 <= token <= 0xE6:
                reader.pos += 1
                repeat = token - 0xE3
                if not values:
                    raise ValueError("repeat without a previous value")
                values.extend([values[-1]] * repeat)
                continue
            if token == 0xF7:
                reader.pos += 1
                field_id = reader.compact_int()
                values.append(Node("<ref>", 0xF7, field_id))
                continue
            if token == 0xFB:
                reader.pos += 1
                break
            if token in (0xE0, 0xE2, 0xE3) or 0xF1 <= token <= 0xF4:
                break
            if type_id == 0x00:
                values.append(reader.compact_int())
            else:
                values.append(self.ReadScalar(type_id))
        return values

    def Pop(self, count: int) -> None:
        for _ in range(count):
            if len(self.stack) > 1:
                self.stack.pop()

    def ReadValue(self, type_id: int, count: int | None) -> object:
        reader = self.reader
        if reader.pos < len(reader.data) and reader.data[reader.pos] == 0xE1:
            reader.pos += 1
            return None
        if reader.pos < len(reader.data) and reader.data[reader.pos] in (0xE2, 0xE3):
            token = reader.byte()
            self.stack.append([])
            return Node("<begin>", token)
        if reader.pos < len(reader.data) and reader.data[reader.pos] in (0xF8, 0xF9):
            if reader.data[reader.pos] == 0xF8:
                reader.pos += 1
                count = reader.compact_int()
            else:
                reader.pos += 1
                rows = reader.compact_int()
                cols = reader.compact_int()
                count = rows * cols
            return self.ReadArray(type_id, count)
        if type_id == 0x00:
            return reader.compact_int()
        return self.ReadScalar(type_id)

    def ReadField(self, field_def: FieldDef) -> Node:
        reader = self.reader
        while reader.pos < len(reader.data) and 0xF1 <= reader.data[reader.pos] <= 0xF4:
            close = reader.data[reader.pos] - 0xF0
            reader.pos += 1
            self.Pop(close)
        node = Node(field_def.name, field_def.type_id)
        if field_def.count is not None and field_def.type_id != 0x00:
            node.value = self.ReadArray(field_def.type_id, field_def.count)
        else:
            node.value = self.ReadValue(field_def.type_id, field_def.count)
            if isinstance(node.value, list) and field_def.type_id != 0x00:
                field_def.count = len(node.value)
        self.nodes.append(node)
        return node

    def Run(self) -> list[Node]:
        reader = self.reader
        while reader.pos < len(reader.data):
            token = reader.data[reader.pos]
            if token == 0xE0:
                reader.pos += 1
                type_id = reader.byte()
                name = reader.cstring()
                field_def = FieldDef(name, type_id)
                self.fields.append(field_def)
                self.index = len(self.fields) - 1
                self.stack[-1].append(self.index)
                if name == "first_feat_ptr":
                    self.feature_start = len(self.fields)
                node = self.ReadField(field_def)
                self.index += 1
                if name == "next_feat_ptr" and isinstance(node.value, Node):
                    self.index = self.feature_start
                continue
            if 0xF1 <= token <= 0xF4:
                reader.pos += 1
                self.Pop(token - 0xF0)
                continue
            if token == 0xF7:
                reader.pos += 1
                field_id = reader.compact_int()
                if 1 <= field_id <= len(self.fields):
                    self.index = field_id - 1
                    field_def = self.fields[self.index]
                    node = self.ReadField(field_def)
                    self.index += 1
                    if field_def.name == "next_feat_ptr" and isinstance(node.value, Node):
                        self.index = self.feature_start
                else:
                    self.nodes.append(Node("<ref>", 0xF7, field_id))
                continue
            if self.index < len(self.fields):
                field_def = self.fields[self.index]
                node = self.ReadField(field_def)
                self.index += 1
                if field_def.name == "next_feat_ptr" and isinstance(node.value, Node):
                    self.index = self.feature_start
                continue
            if token in (0xE2, 0xE3):
                reader.pos += 1
                self.stack.append([])
                self.nodes.append(Node("<begin>", token))
                continue
            if token == 0xE1:
                reader.pos += 1
                self.nodes.append(Node("<null>", 0xE1))
                continue
            raise ValueError(f"unexpected token {token:#04x} at {reader.pos:#x}")
        return self.nodes


    def Features(self) -> list[dict[str, object]]:
        features: list[dict[str, object]] = []
        current: dict[str, object] = {}
        for node in self.nodes:
            if node.name in ("first_feat_ptr", "next_feat_ptr"):
                if current:
                    features.append(current)
                current = {}
            elif node.name in ("id", "type", "sect_name"):
                current[node.name] = node.value
        if current:
            features.append(current)
        return features


def Dump(nodes: list[Node], depth: int = 0) -> None:
    for node in nodes:
        if node.type_id == 0x00 and isinstance(node.value, list):
            print(f"{'  ' * depth}{node.name} {{")
            Dump(node.value, depth + 1)
            print(f"{'  ' * depth}}}")
        else:
            print(f"{'  ' * depth}{node.name} = {node.value!r}")


if __name__ == "__main__":
    path = Path(sys.argv[1])
    parser = Parser(path.read_bytes())
    try:
        nodes = parser.Run()
    except ValueError as ErrorInfo:
        print(f"# stopped at {parser.reader.pos:#x}: {ErrorInfo}")
        nodes = parser.nodes
    if len(sys.argv) > 2 and sys.argv[2] == "--features":
        for feature in parser.Features():
            print(feature)
    else:
        Dump(nodes)
