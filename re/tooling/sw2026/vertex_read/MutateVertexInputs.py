from dataclasses import replace
from struct import pack
from types import MappingProxyType

from convert import open_document
from convert.Geometry.Parasolid import KMissingParam, ParaHeaderData, ReadBrepResult
from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.LocalWrite.WriteXmtNodeMut import WriteXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
from convert.adapters.solidworks.Archive.Partition.ReadXmtNodeMut import ReadXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor

from FixtureGeometry import check_geometry


def selected_records(payload):
    header = ParaHeaderData(payload)
    body = payload[header.body_offset:]
    cursor = XmtCursor(body)
    chosen = {}
    while True:
        start = cursor.OffsetValue
        seen = set(cursor.SeenKinds)
        kind = cursor.ReadKind()
        if kind == 1:
            break
        node = ReadXmtNodeMut(cursor, kind)
        if kind in (18, 30, 50) and kind not in chosen:
            encoded = bytearray()
            WriteXmtNodeMut(encoded, node, KKernelShapes[kind], seen)
            assert bytes(encoded) == body[start:cursor.OffsetValue]
            chosen[kind] = (start, cursor.OffsetValue, node)
    cursor.FinishRead()
    assert set(chosen) == {18, 30, 50}
    return header, body, chosen


def numerical_faults(payload, repack, refuse, five):
    header, body, chosen = selected_records(payload)
    start, end, node = chosen[18]
    sentinel = pack(">d", KMissingParam)
    assert node.FieldsValue["tolerance"] == KMissingParam and body[start:end].count(sentinel) == 1
    offset = start + body[start:end].index(sentinel)
    results = {}
    for name, value in (("nan_tolerance", float("nan")), ("infinite_tolerance", float("inf")),
                        ("negative_tolerance", -1e-8), ("large_tolerance", 1e100)):
        changed = payload[:header.body_offset + offset] + pack(">d", value) + payload[header.body_offset + offset + 8:]
        CheckXmtGraph(ReadActiveNodes(changed))
        legacy, reason = ReadBrepResult(changed)
        assert legacy is None
        results[name] = {"legacy_reason": reason, "public": refuse(repack(changed)), "typed_graph_valid": True}
    finite = payload[:header.body_offset + offset] + pack(">d", 1e-8) + payload[header.body_offset + offset + 8:]
    CheckXmtGraph(ReadActiveNodes(finite))
    document = open_document(repack(finite), source_format="solidworks.sldprt", strict=True,
                             include_brep=True, include_tessellation=False)
    geometry = check_geometry(document, five)
    assert any(abs(vertex.tolerance - 1e-5) < 1e-16 for vertex in document.brep.vertices)
    results["finite_tolerance"] = {"public": geometry, "tolerance_mm": 1e-5}
    return results


def owner_faults(payload, repack, refuse):
    header, body, chosen = selected_records(payload)
    results = {}
    for kind in (30, 50):
        start, end, node = chosen[kind]
        prefix = XmtCursor(body)
        while prefix.OffsetValue < start:
            current = prefix.ReadKind()
            ReadXmtNodeMut(prefix, current)
        seen = set(prefix.SeenKinds)
        replacement = replace(node, FieldsValue=MappingProxyType(dict(node.FieldsValue) | {"owner": 1}))
        encoded = bytearray()
        WriteXmtNodeMut(encoded, replacement, KKernelShapes[kind], seen)
        changed = payload[:header.body_offset + start] + bytes(encoded) + payload[header.body_offset + end:]
        CheckXmtGraph(ReadActiveNodes(changed))
        legacy, reason = ReadBrepResult(changed)
        assert legacy is None
        results["wrong_line_owner" if kind == 30 else "wrong_plane_owner"] = {
            "legacy_reason": reason, "public": refuse(repack(changed)), "typed_graph_valid": True}
    return results
