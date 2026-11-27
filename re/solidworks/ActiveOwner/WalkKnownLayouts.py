from argparse import ArgumentParser
from collections import Counter
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

if not __debug__:
    raise RuntimeError("run without Python optimization to preserve evidence checks")

parser = ArgumentParser()
parser.add_argument("--trim-authority", type=Path, required=True)
parser.add_argument("--owner-authority", type=Path, required=True)
parser.add_argument("--source", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
sha = lambda b: sha256(b).hexdigest()
assert not args.output.exists(), "output directory must be absent"
original_schema = dict(KKernelShapes)
assert 133 not in original_schema and 141 not in original_schema
specs = {
    133: (
        "TRIMMED_CURVE",
        "node_id:d attributes_features:p1019 owner:p1010 next:p1008 previous:p1008 geometric_owner:p141 sense:c basis_curve:p1008 point_1:v point_2:v parm_1:f parm_2:f",
        args.trim_authority,
        "8fb352968f34ccf229e5b97b762c772f55743c8958ab77f8215a834070c763a5",
    ),
    141: (
        "GEOMETRIC_OWNER",
        "owner:p1003 next:p141 previous:p141 shared_geometry:p1003",
        args.owner_authority,
        "e20e859e81c8f71f34629e6ed6aa97affca47bae1a77afaffcf81c71edf847f3",
    ),
}
extra = {}
authorities = {}
for kind, (name, spec, path, expected) in specs.items():
    raw = path.read_bytes()
    assert sha(raw) == expected
    authority = json.loads(raw)
    assert (
        authority["kind"] == kind
        and authority["embedding_base"] == 13006
        and authority["active_schema"] == 37102
    )
    assert (
        authority["kernel"]["sha256"]
        == "2a0b45e9778c42acaa9a955d4dd4826c8892ac3be08532b819778c7989c66969"
    )
    assert authority["typed_field_spec"] == spec
    shape = MakeXmtShape(name, spec)
    assert SchemaHeader(shape) == b"\xff"
    fields = [
        (f.NameValue, f.EncodingValue, f.PointerClass, f.CountValue)
        for f in shape.FieldsValue
    ]
    for key in ("base_layout", "current_layout"):
        layout = authority[key]
        assert layout["name"] == name and layout["class_transmittable"] is True
        assert all(f["transferred"] is True for f in layout["fields"])
        assert [
            (f["name"], f["encoding"], f["pointer_class"], f["count"])
            for f in layout["fields"]
        ] == fields
    extra[kind] = shape
    authorities[str(kind)] = {"file": path.name, "sha256": sha(raw), "field_spec": spec}
source = args.source.read_bytes()
assert sha(source) == "dcea552fa4751563c124fb1dc571f3e0b36c0ce37ce39610b45f7717d8687115"
archive = SldprtArchive.from_bytes(source)
stream = "Contents/Config-0-Partition"
wire = archive.Require(stream)
payloads = DecodePartition(wire, stream)
(active,) = (p for p in payloads if p.kind == "partition")
assert (
    active.sha256 == "af3dd2ac0b09608ef1d48207b0cce8d0a395fdc4adabd97a53522e12c4c9cf56"
)
header = ParaHeaderData(active.data)
assert header is not None and header.schema == "SCH_3701250_37102_13006"
assert (
    header.description
    == ": TRANSMIT FILE (partition) created by modeller version 3701250"
)
body = active.data[header.body_offset :]
cursor = XmtCursor(body)
nodes = {}
records = []
refusal = None
terminator = None


def safe(value):
    if isinstance(value, bytes):
        return {"$bytes_hex": value.hex()}
    if isinstance(value, dict):
        return {k: safe(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [safe(v) for v in value]
    return value


def float_words(value):
    if type(value) is float:
        return value.hex()
    if isinstance(value, (tuple, list)):
        return [float_words(v) for v in value]
    return None


while True:
    start = cursor.OffsetValue
    kind = cursor.ReadKind()
    if kind == 1:
        cursor.FinishRead()
        terminator = {
            "body_span": [start, cursor.OffsetValue],
            "wire_sha256": sha(body[start : cursor.OffsetValue]),
        }
        break
    schema = extra.get(kind, original_schema.get(kind))
    values = []

    def read_value(current, field, previous=False):
        position = current.OffsetValue
        value = ReadXmtValueMut(current, field, previous)
        values.append(
            {
                "field": field.NameValue,
                "encoding": field.EncodingValue,
                "pointer_class": field.PointerClass,
                "body_span": [position, current.OffsetValue],
                "wire_hex": body[position : current.OffsetValue].hex(),
                "value": safe(value),
            }
        )
        return value

    try:
        first = kind not in cursor.SeenKinds
        if kind in extra:
            if first:
                cursor.ExpectBytes(SchemaHeader(schema))
                cursor.SeenKinds.add(kind)
            index = cursor.ReadIndex()
            fields = {}
            for field in schema.FieldsValue:
                if field.EncodingValue == "c":
                    position = cursor.OffsetValue
                    value = cursor.TakeBytes(1).decode("ascii")
                    values.append(
                        {
                            "field": field.NameValue,
                            "encoding": "c",
                            "pointer_class": 0,
                            "body_span": [position, cursor.OffsetValue],
                            "wire_hex": body[position : cursor.OffsetValue].hex(),
                            "value": value,
                        }
                    )
                else:
                    value = read_value(cursor, field)
                fields[field.NameValue] = value
            node = XmtNode(index, kind, MappingProxyType(fields))
        else:
            node = ReadXmtNodeMut(cursor, kind, ValueReader=read_value)
        assert (
            node.IndexValue and node.IndexValue not in nodes
        ), "duplicate or null index"
        assert (
            kind not in (3, 4) and len(nodes) < 4096
        ), "active profile exceeds ownership bound"
        assert set(node.FieldsValue) == {
            f.NameValue for f in schema.FieldsValue
        }, "field set differs"
        nodes[node.IndexValue] = node
        pointers = []
        for field in schema.FieldsValue:
            if field.EncodingValue != "p":
                continue
            refs = (
                node.Indexes(field.NameValue)
                if field.CountValue
                else (node.Integer(field.NameValue),)
            )
            pointers.extend(
                {
                    "field": field.NameValue,
                    "ordinal": i,
                    "pointer_class": field.PointerClass,
                    "target": target,
                    "null": target == 0,
                }
                for i, target in enumerate(refs)
            )
        records.append(
            {
                "index": node.IndexValue,
                "kind": kind,
                "first_use": first,
                "body_span": [start, cursor.OffsetValue],
                "payload_span": [
                    start + header.body_offset,
                    cursor.OffsetValue + header.body_offset,
                ],
                "wire_sha256": sha(body[start : cursor.OffsetValue]),
                "fields": safe(dict(node.FieldsValue)),
                "float_words": {
                    key: float_words(value)
                    for key, value in node.FieldsValue.items()
                    if type(value) is float or isinstance(value, (tuple, list))
                },
                "scalar_wire": values,
                "pointers": pointers,
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
complete = terminator is not None
missing = []
for record in records:
    for pointer in record["pointers"]:
        target = pointer["target"]
        pointer["target_kind"] = nodes[target].KindValue if target in nodes else None
        if target and target not in nodes:
            missing.append(
                {
                    "owner_index": record["index"],
                    "owner_kind": record["kind"],
                    **pointer,
                }
            )
worlds = [n for n in nodes.values() if n.KindValue == 101]
world_valid = (
    len(worlds) == 1 and worlds[0].IndexValue == 1 and worlds[0].Integer("alive") == 1
)
assert records[0]["body_span"][0] == 6
assert all(a["body_span"][1] == b["body_span"][0] for a, b in zip(records, records[1:]))
if complete:
    assert records[-1]["body_span"][1] == terminator["body_span"][0] and terminator[
        "body_span"
    ][1] == len(body)
assert dict(KKernelShapes) == original_schema and args.source.read_bytes() == source
result = {
    "schema": "kit.research.p03-known-layout-walk.v1",
    "source_file": args.source.name,
    "source_sha256": sha(source),
    "source_bytes": len(source),
    "stream": stream,
    "stream_sha256": sha(wire),
    "active_payload_sha256": active.sha256,
    "active_payload_bytes": len(active.data),
    "body_offset": header.body_offset,
    "body_bytes": len(body),
    "profile": {"schema": header.schema, "description": header.description},
    "authorities": authorities,
    "method_sha256": sha(Path(__file__).read_bytes()),
    "physical_complete": complete,
    "first_refusal": refusal,
    "node_count": len(nodes),
    "kind_counts": dict(sorted(Counter(n.KindValue for n in nodes.values()).items())),
    "world_alive_unique_index1": world_valid,
    "all_declared_pointer_targets_exist": not missing,
    "unresolved_pointers": missing,
    "records": records,
    "terminator": terminator,
    "sdk_schema_unmodified": True,
    "public_decoder_calls": 0,
    "native_launches": 0,
    "unknown_records_skipped": 0,
    "source_unchanged": True,
    "scope": "exact source/current active profile; two independently proven extra layouts only; target existence is not pointer-domain or whole-source semantic admission",
}
report = (
    json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    + b"\n"
)
summary = {
    key: value
    for key, value in result.items()
    if key not in ("records", "unresolved_pointers")
}
summary["result_sha256"] = sha(report)
summary["unresolved_pointer_count"] = len(missing)
summary["extra_rows"] = [r for r in records if r["kind"] in extra]
summary_raw = (
    json.dumps(summary, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    + b"\n"
)
if complete:
    assert world_valid and not missing, "complete graph failed world/reference check"
for kind, (_, _, path, expected) in specs.items():
    assert sha(path.read_bytes()) == expected, f"kind {kind} descriptor changed"
args.output.mkdir(exist_ok=False)
(args.output / "Result.json").write_bytes(report)
(args.output / "Summary.json").write_bytes(summary_raw)
print(
    json.dumps(
        {
            "result_sha256": sha(report),
            "summary_sha256": sha(summary_raw),
            "method_sha256": result["method_sha256"],
            "physical_complete": complete,
            "node_count": len(nodes),
            "kind_counts": result["kind_counts"],
            "next_refusal": refusal,
            "world_valid": world_valid,
            "unresolved_pointers": len(missing),
        },
        sort_keys=True,
    )
)
