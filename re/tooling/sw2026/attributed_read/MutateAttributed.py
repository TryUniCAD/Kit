from dataclasses import replace
from struct import pack
from types import MappingProxyType

from convert.Geometry.Parasolid import EncodePartMut, ParaHeaderData
from convert.adapters.solidworks.Container.Parasolid import DecodePartition
from convert.adapters.solidworks.Archive.Partition.Current.Attributed.AttributedShapes import KAttributedShapes
from convert.adapters.solidworks.Archive.Partition.LocalWrite.WriteXmtNodeMut import WriteXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.ReadXmtShapeMut import ReadXmtShapeMut
from convert.adapters.solidworks.Archive.Partition.ReadXmtValueMut import ReadXmtValueMut
from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor

from AdapterBoundary import STREAM


def record_slots(payload):
    header = ParaHeaderData(payload)
    assert header is not None
    body = payload[header.body_offset:]
    cursor = XmtCursor(body)
    records = []
    while True:
        start = cursor.OffsetValue
        seen = set(cursor.SeenKinds)
        kind = cursor.ReadKind()
        if kind == 1:
            break
        scalar_positions = []
        def read_value(current, field, previous=False):
            position = current.OffsetValue
            value = ReadXmtValueMut(current, field, previous)
            scalar_positions.append((field.NameValue, field.EncodingValue, position, current.OffsetValue))
            return value
        node = ReadXmtShapeMut(cursor, kind, KAttributedShapes[kind], ValueReader=read_value)
        encoded = bytearray()
        WriteXmtNodeMut(encoded, node, KAttributedShapes[kind], set(seen))
        assert bytes(encoded) == body[start:cursor.OffsetValue]
        records.append((start, cursor.OffsetValue, seen, node, scalar_positions))
    cursor.FinishRead()
    return header, body, records


def rewrite(payload, layout, predicate, changes):
    header, body, records = layout
    start, end, seen, node, _ = next(row for row in records if predicate(row[3]))
    altered = replace(node, FieldsValue=MappingProxyType(dict(node.FieldsValue) | changes(node)))
    encoded = bytearray()
    WriteXmtNodeMut(encoded, altered, KAttributedShapes[node.KindValue], set(seen))
    return payload[:header.body_offset + start] + bytes(encoded) + payload[header.body_offset + end:]


def raw_scalar(payload, layout, kind, encoding, value):
    header, _, records = layout
    _, _, _, node, positions = next(row for row in records if row[3].KindValue == kind)
    name, code, start, end = next(p for p in positions if p[1] == encoding)
    assert code == "f" and end - start == 8
    return payload[:header.body_offset + start] + pack(">d", value) + payload[header.body_offset + end:]


def repack(native, changed):
    wire = b"".join(EncodePartMut(changed if p.kind == "partition" else p.data) for p in native)
    return DecodePartition(wire, STREAM)
