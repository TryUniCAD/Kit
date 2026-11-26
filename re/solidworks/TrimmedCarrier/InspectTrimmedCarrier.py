from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
import json
from convert.Geometry.Parasolid import ParaHeaderData
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Parasolid import DecodePartition
from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.MakeXmtShape import MakeXmtShape
from convert.adapters.solidworks.Archive.Partition.ReadXmtNodeMut import ReadXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.ReadXmtValueMut import (
    ReadXmtValueMut,
)
from convert.adapters.solidworks.Archive.Partition.SchemaHeader import SchemaHeader
from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Archive.Partition.XmtReferences import XmtReferences

if not __debug__:
    raise RuntimeError("run without Python optimization to preserve evidence checks")

parser = ArgumentParser()
parser.add_argument("--authority", type=Path, required=True)
parser.add_argument("--source", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
sha = lambda data: sha256(data).hexdigest()
authority = args.authority.read_bytes()
assert (
    sha(authority) == "8fb352968f34ccf229e5b97b762c772f55743c8958ab77f8215a834070c763a5"
)
authority_record = json.loads(authority)
expected_spec = "node_id:d attributes_features:p1019 owner:p1010 next:p1008 previous:p1008 geometric_owner:p141 sense:c basis_curve:p1008 point_1:v point_2:v parm_1:f parm_2:f"
assert authority_record["schema"] == "kit.sw2026.p03.trimmed-carrier-static-loader.v1"
assert (
    authority_record["kind"] == 133
    and authority_record["kind_label"] == "TRIMMED_CURVE"
)
assert authority_record["typed_field_spec"] == expected_spec
assert (
    authority_record["embedding_base"] == 13006
    and authority_record["active_schema"] == 37102
)
assert (
    authority_record["kernel"]["sha256"]
    == "2a0b45e9778c42acaa9a955d4dd4826c8892ac3be08532b819778c7989c66969"
)
assert (
    authority_record["equal_effective_wire_layout"] is True
    and authority_record["equal_first_use_marker"] == 255
)
output = args.output.resolve()
assert not output.exists(), "output directory must be absent"
assert args.authority.is_file() and args.source.is_file()
shape = MakeXmtShape("TRIMMED_CURVE", expected_spec)
assert len(shape.FieldsValue) == 12 and SchemaHeader(shape) == b"\xff"
expected_fields = [
    {
        "name": f.NameValue,
        "encoding": f.EncodingValue,
        "pointer_class": f.PointerClass,
        "count": f.CountValue,
    }
    for f in shape.FieldsValue
]
for layout_name in ("base_layout", "current_layout"):
    layout = authority_record[layout_name]
    assert layout["name"] == "TRIMMED_CURVE" and layout["class_transmittable"] is True
    assert all(f["transferred"] is True for f in layout["fields"])
    assert [
        {key: field[key] for key in ("name", "encoding", "pointer_class", "count")}
        for field in layout["fields"]
    ] == expected_fields
assert 133 not in KKernelShapes
original_schema = dict(KKernelShapes)
source = args.source.resolve(strict=True)
raw = source.read_bytes()
assert sha(raw) == "dcea552fa4751563c124fb1dc571f3e0b36c0ce37ce39610b45f7717d8687115"
archive = SldprtArchive.from_bytes(raw)
(active,) = (
    p
    for p in DecodePartition(archive.Require("Contents/Config-0-Partition"))
    if p.kind == "partition"
)
assert (
    active.sha256 == "af3dd2ac0b09608ef1d48207b0cce8d0a395fdc4adabd97a53522e12c4c9cf56"
)
header = ParaHeaderData(active.data)
assert header is not None and header.schema == "SCH_3701250_37102_13006"
body = active.data[header.body_offset :]
cursor = XmtCursor(body)
nodes = {}
records = []
refusal = None
while True:
    start = cursor.OffsetValue
    kind = cursor.ReadKind()
    if kind == 1:
        cursor.FinishRead()
        break
    try:
        widths = []
        if kind == 133:
            first = kind not in cursor.SeenKinds
            if first:
                cursor.ExpectBytes(SchemaHeader(shape))
                cursor.SeenKinds.add(kind)
            index_start = cursor.OffsetValue
            index = cursor.ReadIndex()
            assert index and index not in nodes
            widths.append(
                {
                    "field": "transmitted_index",
                    "body_start": index_start,
                    "width": cursor.OffsetValue - index_start,
                    "value": index,
                }
            )
            fields = {}
            for field in shape.FieldsValue:
                position = cursor.OffsetValue
                value = (
                    cursor.TakeBytes(1).decode("ascii")
                    if field.EncodingValue == "c"
                    else ReadXmtValueMut(cursor, field)
                )
                fields[field.NameValue] = value
                widths.append(
                    {
                        "field": field.NameValue,
                        "body_start": position,
                        "width": cursor.OffsetValue - position,
                        "encoding": field.EncodingValue,
                        "pointer_class": field.PointerClass,
                        "value": value,
                    }
                )
            node = XmtNode(index, kind, MappingProxyType(fields))
        else:
            node = ReadXmtNodeMut(cursor, kind)
            first = None
        assert node.IndexValue not in nodes
        nodes[node.IndexValue] = node
        records.append(
            {
                "index": node.IndexValue,
                "kind": kind,
                "body_span": [start, cursor.OffsetValue],
                "payload_span": [
                    start + header.body_offset,
                    cursor.OffsetValue + header.body_offset,
                ],
                "first_use": first,
                "wire_sha256": sha(body[start : cursor.OffsetValue]),
                "fields": dict(node.FieldsValue),
                "field_widths": widths,
            }
        )
    except (ValueError, KeyError) as failure:
        refusal = {
            "kind": kind,
            "body_start": start,
            "cursor": cursor.OffsetValue,
            "message": str(failure),
            "completed_records": len(records),
        }
        break
carriers = []
for rec in records:
    if rec["kind"] != 133:
        continue
    index = rec["index"]
    consumers = [
        {"index": n.IndexValue, "kind": n.KindValue, "field": "curve"}
        for n in nodes.values()
        if n.KindValue in (16, 17) and n.FieldsValue.get("curve") == index
    ]
    resolved_refs = [
        {
            "field": f.NameValue,
            "pointer_class": f.PointerClass,
            "index": rec["fields"][f.NameValue],
            "target_kind": (
                nodes[rec["fields"][f.NameValue]].KindValue
                if rec["fields"][f.NameValue] in nodes
                else None
            ),
            "null": rec["fields"][f.NameValue] == 0,
        }
        for f in shape.FieldsValue
        if f.EncodingValue == "p"
    ]
    carriers.append(
        {
            "index": index,
            "transmitted_reference": index + 1,
            "body_span": rec["body_span"],
            "payload_span": rec["payload_span"],
            "fields": rec["fields"],
            "field_widths": rec["field_widths"],
            "references": resolved_refs,
            "edge_or_fin_consumers": consumers,
            "consumed_by_edge_or_fin_in_complete_prefix": bool(consumers),
        }
    )
missing = []
for node in nodes.values():
    refs = (
        [node.Integer(f.NameValue) for f in shape.FieldsValue if f.EncodingValue == "p"]
        if node.KindValue == 133
        else list(XmtReferences(node))
    )
    missing.extend(
        {"owner_index": node.IndexValue, "owner_kind": node.KindValue, "target": ref}
        for ref in refs
        if ref and ref not in nodes
    )
first = carriers[0]
assert first["body_span"] == [1840, 1926] and first["index"] == 6
(next_record,) = (r for r in records if r["body_span"][0] == 1926)
assert source.read_bytes() == raw and 133 not in KKernelShapes
result = {
    "schema": "kit.research.p03-kind133-authority-walk.v1",
    "source_sha256": sha(raw),
    "active_payload_sha256": active.sha256,
    "authority_sha256": sha(authority),
    "authority_file": args.authority.name,
    "source_file": source.name,
    "method_sha256": sha(Path(__file__).read_bytes()),
    "declared_schema": {
        "name": shape.NameValue,
        "fields": [
            {
                "name": f.NameValue,
                "encoding": f.EncodingValue,
                "pointer_class": f.PointerClass,
                "count": f.CountValue,
            }
            for f in shape.FieldsValue
        ],
    },
    "completed": refusal is None,
    "next_refusal": refusal,
    "completed_nodes": len(nodes),
    "all_references_resolve": not missing,
    "unresolved_refs": missing,
    "carrier_count": len(carriers),
    "carriers": carriers,
    "first_next_actual_record": next_record,
    "records": records,
    "public_decoder_calls": 0,
    "native_launches": 0,
    "unknown_records_skipped": 0,
    "sdk_schema_unmodified": True,
    "helper_file_sha256": {
        f.__module__ + "." + f.__name__: sha(Path(f.__code__.co_filename).read_bytes())
        for f in (ReadXmtNodeMut, ReadXmtValueMut, SchemaHeader)
    },
    "scope": "research-only exact kind133 known grammar; consumer absence is prefix-only; next unknown refuses; no public SDK repair or projection",
}
report = json.dumps(result, sort_keys=True, separators=(",", ":")).encode() + b"\n"
assert (
    dict(KKernelShapes) == original_schema and args.authority.read_bytes() == authority
)
output.mkdir(exist_ok=False)
(output / "Result.json").write_bytes(report)
print(
    json.dumps(
        {
            "report_sha256": sha(report),
            "method_sha256": result["method_sha256"],
            "completed": result["completed"],
            "nodes": len(nodes),
            "next_refusal": refusal,
            "unresolved_count": len(missing),
            "carrier_count": len(carriers),
            "first_next_actual": {
                "index": next_record["index"],
                "kind": next_record["kind"],
                "body_span": next_record["body_span"],
            },
            "carriers": [
                {
                    "index": c["index"],
                    "span": c["body_span"],
                    "points": [c["fields"]["point_1"], c["fields"]["point_2"]],
                    "parameters": [c["fields"]["parm_1"], c["fields"]["parm_2"]],
                    "basis": c["fields"]["basis_curve"],
                    "consumers": c["edge_or_fin_consumers"],
                }
                for c in carriers
            ],
        },
        sort_keys=True,
    )
)
