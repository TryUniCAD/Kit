"""Research-only tagged-stream parser for Creo PSB sections.

The grammar is the one recorded in `re/creo/data-model/DataModel.md` and confirmed
against the `ugc_read_structure` and `ugc_ieee_unformat_double` decompilations in
`re/creo/loader/Loader.md`. This module is not production code; it exists to
validate the field map against the empty control and the one-feature ladder.

The parser propagates the `f1`-`f4` close count up the recursion and caches one
field schema per structure name, so the second and later feature records reuse the
first record's field table.
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
        self.schemas: dict[str, list[tuple[str, int]]] = {}

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

    def ReadValue(
        self,
        type_id: int,
        schema: list[tuple[str, int]],
        field_name: str | None = None,
        allow_array: bool = True,
    ) -> tuple[object, int]:
        reader = self.reader
        while reader.pos < len(reader.data) and 0xF1 <= reader.data[reader.pos] <= 0xF4:
            reader.pos += 1
        if reader.pos < len(reader.data) and reader.data[reader.pos] == 0xE1:
            reader.pos += 1
            return (None, 0)
        if allow_array and reader.pos < len(reader.data) and reader.data[reader.pos] in (0xF8, 0xF9):
            if reader.data[reader.pos] == 0xF8:
                reader.pos += 1
                count = reader.compact_int()
            else:
                reader.pos += 1
                rows = reader.compact_int()
                cols = reader.compact_int()
                count = rows * cols
            return (self.ReadArray(type_id, schema, count), 0)
        if type_id == 0x00:
            token = reader.byte()
            if token in (0xE2, 0xE3):
                return self.ReadFields(1, field_name)
            raise ValueError(
                f"structure value expected e2/e3, got {token:#04x} at {reader.pos - 1:#x}"
            )
        if type_id in (0x01, 0x05, 0x07, 0x08, 0x09, 0x0B):
            return (reader.compact_int(), 0)
        if type_id == 0x02:
            return (self.ReadDouble(), 0)
        if type_id in (0x03, 0x0A):
            return (reader.cstring(), 0)
        if type_id == 0x04:
            return (reader.byte(), 0)
        if type_id == 0x06:
            return (struct.unpack(">f", reader.take(4))[0], 0)
        raise ValueError(f"unknown field type {type_id:#04x} at {reader.pos:#x}")

    def ReadArray(
        self, type_id: int, schema: list[tuple[str, int]], count: int | None
    ) -> list[object]:
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
            value, _ = self.ReadValue(type_id, schema, allow_array=False)
            values.append(value)
        return values

    def SchemaFor(self, key: str | None) -> list[tuple[str, int]]:
        if key is None:
            return []
        return self.schemas.setdefault(key, [])

    def ReadFields(self, depth: int, schema_key: str | None) -> tuple[list[Node], int]:
        reader = self.reader
        nodes: list[Node] = []
        schema = self.SchemaFor(schema_key)
        current: tuple[str, int] | None = None
        while reader.pos < len(reader.data):
            token = reader.data[reader.pos]
            if token == 0xE0:
                reader.pos += 1
                type_id = reader.byte()
                name = reader.cstring()
                if schema_key is None:
                    schema_key = name
                    schema = self.SchemaFor(schema_key)
                schema.append((name, type_id))
                current = (name, type_id)
                node = Node(name, type_id)
                node.value, close = self.ReadValue(type_id, schema, name)
                nodes.append(node)
                self.nodes.append(node)
                if close > 0:
                    close -= 1
                    if close > 0:
                        return (nodes, close)
                continue
            if 0xF1 <= token <= 0xF4:
                reader.pos += 1
                return (nodes, token - 0xF0 - 1)
            if token == 0xE1:
                reader.pos += 1
                nodes.append(Node("<null>", 0xE1))
                continue
            if token in (0xE2, 0xE3):
                reader.pos += 1
                node = Node("<begin>", token)
                node.value, close = self.ReadFields(1, schema_key)
                nodes.append(node)
                if close > 0:
                    close -= 1
                    if close > 0:
                        return (nodes, close)
                continue
            if token == 0xF7:
                reader.pos += 1
                field_id = reader.compact_int()
                if 1 <= field_id <= len(schema):
                    name, type_id = schema[field_id - 1]
                    current = (name, type_id)
                    node = Node(name, type_id)
                    node.value, close = self.ReadValue(type_id, schema, name)
                    nodes.append(node)
                    self.nodes.append(node)
                    if close > 0:
                        close -= 1
                        if close > 0:
                            return (nodes, close)
                else:
                    nodes.append(Node("<ref>", 0xF7, field_id))
                continue
            if token in (0xF8, 0xF9) and current is not None:
                name, type_id = current
                node = Node(name, type_id)
                node.value, close = self.ReadValue(type_id, schema, name)
                nodes.append(node)
                self.nodes.append(node)
                if close > 0:
                    close -= 1
                    if close > 0:
                        return (nodes, close)
                continue
            if token in (0xE4, 0xE5, 0xE6, 0xE7, 0xFA, 0xFB):
                nodes.append(Node("<control>", token))
                reader.pos += 1
                continue
            if current is not None:
                name, type_id = current
                node = Node(name, type_id)
                node.value, close = self.ReadValue(type_id, schema, name, allow_array=False)
                nodes.append(node)
                self.nodes.append(node)
                if close > 0:
                    close -= 1
                    if close > 0:
                        return (nodes, close)
                continue
            raise ValueError(f"unexpected token {token:#04x} at {reader.pos:#x}")
        return (nodes, 0)


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
        nodes, _ = parser.ReadFields(0, None)
    except ValueError as ErrorInfo:
        print(f"# stopped at {parser.reader.pos:#x}: {ErrorInfo}")
        nodes = parser.nodes
    Dump(nodes)
