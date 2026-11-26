from struct import pack

from convert.Geometry.Parasolid import EncodePartMut, ParaHeaderData
from convert.adapters.solidworks.Container.Container import SldprtFormatError
from convert.adapters.solidworks.Container.Parasolid import DecodePartition
from convert.adapters.solidworks.Core.Partition.ActivePartition import ReadActivePart

from AdapterBoundary import BODY, STREAM, bind
from MutateAttributed import raw_scalar, record_slots, repack, rewrite


def check_faults(native, active):
    payload = active.data
    layout = record_slots(payload)
    header = ParaHeaderData(payload)
    assert header is not None
    nodes = {row[3].IndexValue: row[3] for row in layout[2]}
    body, = (node for node in nodes.values() if node.KindValue == 12)
    solid = nodes[body.Integer("shell")]
    void, = (node for node in nodes.values() if node.KindValue == 13 and node.IndexValue != solid.IndexValue)
    face = solid.Integer("face")
    assert face and nodes[face].KindValue == 14
    assert solid.Integer("front_face") == 0 and void.Integer("face") == 0
    candidates = {
        "solid_complementary_front_face": rewrite(payload, layout, lambda n: n.IndexValue == solid.IndexValue, lambda n: {"front_face": face}),
        "void_complementary_face": rewrite(payload, layout, lambda n: n.IndexValue == void.IndexValue, lambda n: {"face": face}),
        "truncated_active": payload[:header.body_offset + 8],
        "trailing_active": payload + b"\x00",
        "unsupported_schema": payload.replace(b"SCH_3701250_37102_13006", b"SCH_3701250_37102_13007", 1),
        "attribute_wrong_definition": rewrite(payload, layout, lambda n: n.KindValue == 81, lambda n: {"definition": 1}),
        "attribute_detached_owner": rewrite(payload, layout, lambda n: n.KindValue == 81, lambda n: {"owner": 0}),
        "attribute_nonreciprocal": rewrite(payload, layout, lambda n: n.KindValue == 81 and n.Integer("next_of_type") not in (0, n.IndexValue), lambda n: {"next_of_type": n.IndexValue}),
        "attribute_owner_flags": rewrite(payload, layout, lambda n: n.KindValue == 80 and any(n.FieldsValue["legal_owners"]), lambda n: {"legal_owners": tuple(0 for _ in n.FieldsValue["legal_owners"])}),
        "nonfinite_attribute_value": raw_scalar(payload, layout, 83, "f", float("nan")),
        "zero_plane_normal": rewrite(payload, layout, lambda n: n.KindValue == 50, lambda n: {"normal": (0.0, 0.0, 0.0)}),
        "opposite_face_sense": rewrite(payload, layout, lambda n: n.KindValue == 14, lambda n: {"sense": "+" if n.FieldsValue["sense"] == "-" else "-"}),
        "negative_plane_carrier": rewrite(payload, layout, lambda n: n.KindValue == 50 and n.FieldsValue["sense"] == "+", lambda n: {"sense": "-"}),
        "empty_trim_interval": rewrite(payload, layout, lambda n: n.KindValue == 133, lambda n: {"parm_2": n.FieldsValue["parm_1"]}),
        "wrong_shared_geometry": rewrite(payload, layout, lambda n: n.KindValue == 141, lambda n: {"shared_geometry": 1}),
        "missing_vertex_halfedge": rewrite(payload, layout, lambda n: n.KindValue == 18, lambda n: {"halfedge": 0}),
    }
    start, _, _, _, _ = next(row for row in layout[2] if row[3].KindValue == 133)
    candidates["unknown_physical_kind"] = payload[:header.body_offset + start] + pack(">H", 142) + payload[header.body_offset + start + 2:]
    result = {}
    for name, changed in candidates.items():
        assert changed != payload, name
        rejected, _ = bind(repack(native, changed))
        assert rejected is not None and rejected.ModelValue is None, name
        result[name] = {"model": False}
    malformed = EncodePartMut(payload)[:-1]
    try:
        truncated = DecodePartition(malformed, STREAM)
    except SldprtFormatError as failure:
        assert str(failure)
        result["truncated_active_frame"] = {"format_refusal": str(failure)}
    else:
        rejected, _ = bind(truncated)
        assert rejected is not None and rejected.ModelValue is None
        result["truncated_active_frame"] = {"model": False}
    selected, payloads = bind(native)
    assert selected is not None and selected.ModelValue is not None
    duplicate = ReadActivePart((*payloads, payloads[0]), 0, BODY, (STREAM,))
    assert duplicate is not None and duplicate.ModelValue is None and duplicate.PayloadId is None
    wrong = ReadActivePart(payloads, 1, BODY, (STREAM,))
    assert wrong is not None and wrong.ModelValue is None
    assert ReadActivePart(payloads, None, BODY, (STREAM,)) is None
    result.update({"duplicate_active": {"model": False}, "wrong_configuration": {"model": False}, "unselected_configuration": {"model": False}})
    return result
