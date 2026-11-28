from dataclasses import dataclass
from struct import Struct, pack

from builders.EmptyPartition import (
    INITIAL_PMARK_ID,
    PARTITION_KIND,
    PMARK_KIND,
    SOLIDWORKS_2026,
    TERMINATOR_KIND,
    WORLD_KIND,
    terminate,
    write_schema_difference,
)
from convert.Geometry.Parasolid import DecodePartData, EncodePartData, ParaHeaderData, ParaStream, WritePointerMut
from para.Schema import SCHEMAS


SCALARS = {
    code: Struct(">" + representation)
    for code, representation in (("l", "B"), ("u", "B"), ("d", "i"), ("w", "H"), ("f", "d"), ("v", "ddd"))
}
HEADER = pack(">HI", SOLIDWORKS_2026.maximum_node_types, 0)


def schema_bytes(schema):
    result = bytearray()
    write_schema_difference(result, schema.base, schema.current)
    return bytes(result)


SCHEMA_HEADERS = {kind: schema_bytes(schema) for kind, schema in SCHEMAS.items()}


@dataclass(frozen=True)
class Node:
    index: int
    kind: int
    fields: dict


@dataclass(frozen=True)
class Rollback:
    deleted: tuple[tuple[int, int], ...]
    previous_world: Node


@dataclass(frozen=True)
class History:
    mark: Node
    rollback: Rollback | None


@dataclass(frozen=True)
class Partition:
    nodes: tuple[Node, ...]
    root: Node
    history: tuple[History, ...]


class Cursor:
    def __init__(self, data):
        self.data = data
        self.offset = 0
        self.seen = set()
        self.expect(HEADER)

    def take(self, count):
        end = self.offset + count
        if end > len(self.data):
            raise ValueError(f"truncated Parasolid payload at offset {self.offset}")
        value = self.data[self.offset:end]
        self.offset = end
        return value

    def expect(self, value):
        if self.take(len(value)) != value:
            raise ValueError(f"unexpected Parasolid field at offset {self.offset - len(value)}")

    def integer(self, kind):
        shape = Struct(">" + kind)
        return shape.unpack(self.take(shape.size))[0]

    def pointer(self):
        short = self.integer("h")
        if short > 0:
            return short - 1
        if short == 0:
            raise ValueError("invalid Parasolid transmit index")
        wide = self.integer("H") * 32767 - short - 1
        if wide < 32767:
            raise ValueError("invalid wide Parasolid transmit index")
        return wide

    def value(self, field, previous):
        if field.encoding == "p":
            value = self.pointer()
            if previous:
                if value:
                    raise ValueError("only null references are recognized in the preceding WORLD")
                self.expect(b"\x01")
            return value
        shape = SCALARS[field.encoding]
        values = shape.unpack(self.take(shape.size))
        return values if field.encoding == "v" else values[0]

    def node(self, kind, *, previous=False):
        schema = SCHEMAS.get(kind)
        if schema is None:
            raise ValueError(f"unrecognized 2026 Parasolid node kind {kind}")
        if kind not in self.seen:
            self.expect(SCHEMA_HEADERS[kind])
            self.seen.add(kind)
        variable_length = self.integer("I") if any(field.count == 1 for field in schema.current) else 0
        if variable_length > len(self.data) - self.offset:
            raise ValueError("Parasolid array count exceeds remaining payload")
        index = self.pointer()
        values = {}
        for field in schema.current:
            length = variable_length if field.count == 1 else field.count
            if field.encoding == "c":
                values[field.name] = self.take(length if field.count else 1).decode("ascii")
            elif field.count:
                values[field.name] = tuple(self.value(field, previous) for _ in range(length))
            else:
                values[field.name] = self.value(field, previous)
        return Node(index, kind, values)

    def finish(self):
        if self.pointer() or self.offset != len(self.data):
            raise ValueError("Parasolid terminator or payload boundary differs")


def decode_active(payload):
    cursor = Cursor(payload)
    nodes = []
    while (kind := cursor.integer("H")) != TERMINATOR_KIND:
        nodes.append(cursor.node(kind))
    cursor.finish()
    return tuple(nodes)


def decode_history(payload):
    cursor = Cursor(payload)
    root = cursor.node(cursor.integer("H"))
    history = []
    while (kind := cursor.integer("H")) != TERMINATOR_KIND:
        if kind != PMARK_KIND:
            raise ValueError("partition history member is not a mark")
        mark = cursor.node(kind)
        rollback = None
        if mark.fields["delta_key"]:
            cursor.expect(pack(">HH", TERMINATOR_KIND, 1))
            deleted = []
            while index := cursor.pointer():
                deleted.append((index, cursor.integer("H")))
            if cursor.integer("i") != 1 or cursor.integer("H") != WORLD_KIND:
                raise ValueError("rollback must restore one prior WORLD")
            previous_world = cursor.node(WORLD_KIND, previous=True)
            cursor.expect(pack(">HH", TERMINATOR_KIND, 1))
            rollback = Rollback(tuple(deleted), previous_world)
        history.append(History(mark, rollback))
    cursor.finish()
    return root, tuple(history)


def read_partition(stream):
    payloads = DecodePartData(stream)
    sections = {}
    for name, payload in zip(("partition", "deltas"), payloads, strict=True):
        header = ParaHeaderData(payload.data)
        if header is None or header.schema != SOLIDWORKS_2026.schema or header.description != description(name).decode("ascii"):
            raise ValueError(f"unrecognized {name} transmit version")
        sections[name] = payload.data[header.body_offset:]
    root, history = decode_history(sections["deltas"])
    partition = Partition(decode_active(sections["partition"]), root, history)
    validate(partition)
    return partition


def references(node):
    for field in SCHEMAS[node.kind].current:
        if field.encoding == "p":
            value = node.fields[field.name]
            if field.count:
                yield from filter(None, value)
            elif value:
                yield value


def validate(partition):
    active = {node.index: node for node in partition.nodes}
    marks = {entry.mark.index: entry.mark for entry in partition.history}
    all_indexes = active.keys() | marks.keys() | {partition.root.index}
    if not all(index > 0 for index in all_indexes) or len(all_indexes) != len(partition.nodes) + 1 + len(partition.history):
        raise ValueError("partition has a null or repeated transmit index")
    if 1 not in active or active[1].kind != WORLD_KIND or sum(node.kind == WORLD_KIND for node in partition.nodes) != 1:
        raise ValueError("partition must own one active WORLD at transmit index one")
    if any(node.kind in (PARTITION_KIND, PMARK_KIND) for node in partition.nodes):
        raise ValueError("history records cannot be active nodes")
    if any(ref not in active for node in partition.nodes for ref in references(node)):
        raise ValueError("active partition has a dangling reference")
    world = active[1].fields
    root = partition.root
    if root.kind != PARTITION_KIND or root.fields["current_pmark"] not in marks:
        raise ValueError("history has no selected mark")
    mark_ids = {node.fields["id"] for node in marks.values()}
    if INITIAL_PMARK_ID not in mark_ids or min(mark_ids) != INITIAL_PMARK_ID or len(mark_ids) != len(marks) or root.fields["highest_id"] < max(mark_ids):
        raise ValueError("history mark ids disagree with the partition counter")
    if world["current_id"] != marks[root.fields["current_pmark"]].fields["id"] or world["highest_id"] != root.fields["highest_id"]:
        raise ValueError("active WORLD and partition disagree on the retained history")
    delta_keys = set()
    for entry in partition.history:
        current = entry.mark.fields
        key = current["delta_key"]
        if entry.mark.kind != PMARK_KIND or any(ref not in marks for ref in references(entry.mark)) or current["delta_is_forward"]:
            raise ValueError("history mark link or rollback direction is unsupported")
        prior = current["preceding"]
        following = current["first_following"]
        if (current["next_sibling"] or current["prev_sibling"]
                or prior and (marks[prior].fields["first_following"] != entry.mark.index or marks[prior].fields["id"] >= current["id"])
                or following and marks[following].fields["preceding"] != entry.mark.index):
            raise ValueError("history links are not reciprocal in a linear history")
        if not key:
            if current["id"] != INITIAL_PMARK_ID or prior or entry.rollback:
                raise ValueError("only the initial mark can omit rollback")
            continue
        if key < 0 or key in delta_keys or not prior or entry.rollback is None:
            raise ValueError("a noninitial mark needs a unique rollback handle and prior mark")
        delta_keys.add(key)
        rollback = entry.rollback
        old = rollback.previous_world
        if old.index != 1 or old.kind != WORLD_KIND or any(references(old)):
            raise ValueError("only a rollback to a body-free WORLD is supported")
        deleted = dict(rollback.deleted)
        if len(deleted) != len(rollback.deleted) or any(index not in active or active[index].kind != kind for index, kind in deleted.items()):
            raise ValueError("rollback deletion does not resolve to an active node of the stated kind")


def write_node(result, node, seen, *, previous=False):
    fields = SCHEMAS[node.kind].current
    values = node.fields
    if values.keys() != {field.name for field in fields}:
        raise ValueError(f"kind {node.kind} does not have the complete effective field set")
    result.extend(pack(">H", node.kind))
    if node.kind not in seen:
        result.extend(SCHEMA_HEADERS[node.kind])
        seen.add(node.kind)
    for field in fields:
        if field.count == 1:
            result.extend(pack(">I", len(values[field.name])))
    WritePointerMut(result, node.index)
    for field in fields:
        value = values[field.name]
        if field.count > 1 and len(value) != field.count:
            raise ValueError(f"wrong field length for {field.name}")
        if field.encoding == "c":
            if not field.count and len(value) != 1:
                raise ValueError(f"wrong character count for {field.name}")
            result.extend(value.encode("ascii"))
            continue
        for item in value if field.count else (value,):
            if field.encoding == "p":
                WritePointerMut(result, item)
                if previous:
                    result.append(1)
            else:
                arguments = item if field.encoding == "v" else (item,)
                result.extend(SCALARS[field.encoding].pack(*arguments))


def description(name):
    return f": TRANSMIT FILE ({name}) created by modeller version {SOLIDWORKS_2026.modeller_version}".encode("ascii")


def write_payloads(partition):
    validate(partition)
    active = bytearray(HEADER)
    seen = set()
    for node in partition.nodes:
        write_node(active, node, seen)
    terminate(active)
    deltas = bytearray(HEADER)
    seen = set()
    write_node(deltas, partition.root, seen)
    for entry in partition.history:
        write_node(deltas, entry.mark, seen)
        if entry.rollback:
            terminate(deltas)
            for index, kind in entry.rollback.deleted:
                WritePointerMut(deltas, index)
                deltas.extend(pack(">H", kind))
            WritePointerMut(deltas, 0)
            deltas.extend(pack(">i", 1))
            write_node(deltas, entry.rollback.previous_world, seen, previous=True)
            terminate(deltas)
    terminate(deltas)
    return tuple(
        ParaStream(body, SOLIDWORKS_2026.schema, description(name))
        for name, body in (("partition", active), ("deltas", deltas))
    )


def frame_payloads(payloads):
    return b"".join(EncodePartData(payload) for payload in payloads)
