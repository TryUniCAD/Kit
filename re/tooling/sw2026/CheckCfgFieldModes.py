from argparse import ArgumentParser
from codecs import lookup
from functools import partial
import json
from pathlib import Path
from struct import pack, unpack, unpack_from
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from CheckCfgMembers import digest, require
from CheckCfgOwners import audit_run
from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ExternalFields import KExternalFields
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.MaterialFields import KMaterialFields
from convert.adapters.solidworks.Archive.Bodies.Layouts.ContainerFields import KContainerFields
from convert.adapters.solidworks.Archive.Bodies.Layouts.ReferenceFields import KFrameOwnerFields
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadFieldsMut import ReadFieldsMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadSchemaMut import ReadSchemaMut
from convert.adapters.solidworks.Archive.Config.Link.ReadPartStart import ReadPartStart
from convert.adapters.solidworks.Archive.Header.HeaderRefNodes import HeaderRefNodes
from convert.adapters.solidworks.Archive.Maps.AddEntryMut import AddEntryMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Container.Container import SldprtArchive

MANIFEST = ROOT / "re/solidworks/measurements/2026/ConfigFieldModesSource01.json"
LAYOUTS = {**KContainerFields, **KExternalFields, **KMaterialFields, **KFrameOwnerFields}
PART = RuntimeClass("moPart_c", 1)


def guard_runtime():
    for codec in ("ascii", "latin-1", "cp1252", "utf-16-le"):
        lookup(codec)
    sys.addaudithook(audit_run)


def read_exact(data, node, maps, *, rules=(), schema=None, conditions=0, rejection_offset=None):
    context = BodyContext(19000, LAYOUTS, {}, {}, FlagsValue={"conditions": conditions})
    old_base, old_map = maps.BaseValue, maps.Snapshot()
    cursor = BinaryReader(data)
    reader = GraphReader(cursor, maps, partial(ReadBodyMut, context))
    fields = {}
    frame = ReadFrame(context, reader, FieldScope(fields), node, ReadSchemaMut, ReadFieldsMut)
    try:
        if schema is None:
            ReadFieldsMut(frame, rules)
        else:
            ReadSchemaMut(frame, schema)
    finally:
        current = maps.Snapshot()
        require(maps.BaseValue == old_base and current == old_map and all(
            before is after for before, after in zip(old_map.EntriesValue, current.EntriesValue, strict=True)
        ), "bounded field read changed its shared map")
        if rejection_offset is not None:
            require(cursor.GetOffset() == rejection_offset and not fields,
                    "a rejected component owner consumed bytes or published a field")
    require(reader.Cursor is cursor and cursor.GetRemaining() == 0, "field interval was not consumed exactly")
    return fields


def native_slice(config, expected, prefix, *, rules=(), schema=None):
    start, base, counter = expected["start"]
    end, end_base, end_counter = expected["end"]
    require((base, counter) == (end_base, end_counter) and base == prefix.BaseValue,
            "record is outside the measured map-neutral body profile")
    payload = config[start:end]
    require(len(payload) == end - start and digest(payload) == expected["wire_sha256"],
            "native field interval differs from its reference")
    maps = ArchiveMaps(counter, MapSnapshot(counter, prefix.MapValue.EntriesValue))
    maps.BaseValue = base
    fields = read_exact(payload, prefix.RootValue, maps, rules=rules, schema=schema)
    return payload, fields


def reference_strings(data):
    (count,) = unpack_from("<H", data)
    cursor = 2
    rows = []
    for _ in range(count):
        require(data[cursor:cursor + 3] == b"\xff\xfe\xff", "reference expects the observed Unicode frame")
        length = data[cursor + 3]
        cursor += 4
        end = cursor + length * 2
        rows.append({"s": data[cursor:end].decode("utf-16-le")})
        cursor = end
    require(cursor == len(data), "reference did not consume the string array")
    return {"items": rows, "n": count}


def check_leaf(data, fields, schema, prefix):
    if schema == "moComponent_c":
        require(unpack("<H", data) == (2,) and fields["owner"] is prefix.RootValue,
                "unit component did not resolve the actual part root")
        return {"owner": {"class": PART.NameValue, "schema": PART.SchemaValue, "index": 2}}
    if schema == "su_CStringArray":
        require(fields == reference_strings(data), "string array differs from independent wire decode")
    elif schema == "mgBBox_c.restore":
        require(fields == dict(zip((f"b{i}" for i in range(10)), unpack("<10d", data), strict=True)),
                "bounds differ from independent wire decode")
    else:
        selector, width = unpack("<hf", data)
        require(fields == {"f06": selector, "f00": width}, "line width differs from independent wire decode")
    return fields


def component_refusals(prefix):
    maps = ArchiveMaps(prefix.BaseValue, prefix.MapValue)
    alias, = HeaderRefNodes(prefix.HeaderValue, 19000)
    require(maps.EntryMap[3].EntryValue is alias, "wrong inherited object in slot three")
    other = ArchiveNode(prefix.RootValue.ClassValue, {}, IndexValue=maps.CounterValue)
    slot = AddEntryMut(maps, other)
    require(other.ClassValue == prefix.RootValue.ClassValue and other is not prefix.RootValue
            and maps.EntryMap[slot].EntryValue is other, "the same-class contrast is not a distinct mapped object")
    reports = []
    for label, word, reason in (
            ("null", 0, "requires an existing object"),
            ("header_alias", 3, "differs from its enclosing part"),
            ("distinct_part", slot, "differs from its enclosing part"),
            ("new_class", 0xFFFF, "requires an existing object")):
        try:
            read_exact(pack("<H", word), prefix.RootValue, maps, schema="moComponent_c", rejection_offset=0)
        except ValueError as error:
            require(reason in str(error), "component owner refused for a different reason")
            reports.append({"case": label, "word": word, "diagnostic": str(error), "offset": 0})
        else:
            raise ValueError(f"the reader accepted an invalid component owner: {label}")
    return reports


def native_case(name, root, *, witness_only=False):
    if witness_only:
        from CheckCfgModeNative import check_mode_witnesses
    expected = json.loads(MANIFEST.read_bytes())["controls"][name]
    raw = (root / expected["path"]).read_bytes()
    require(digest(raw) == expected["source_sha256"], "wrong native part")
    archive = SldprtArchive.from_bytes(raw)
    config = archive.require("Contents/Config-0")
    header = archive.require("Contents/Config-0-ModelHeader")
    require(digest(config) == expected["config_sha256"] and digest(header) == expected["header_sha256"],
            "wrong native configuration or model header")
    guard_runtime()
    prefix = ReadPartStart(archive)
    require(prefix.RootValue.IndexValue == 2 and prefix.BaseValue == 4, "wrong inherited part start")
    if witness_only:
        modes = check_mode_witnesses(config, expected["mode_witnesses"], prefix)
        require(not prefix.RootValue.FieldsValue, "the bounded repeat changed its owning part")
        return {"case": name, "runtime_external_accesses": 0, "config_sha256": expected["config_sha256"], **modes}
    items = []
    for row in expected["normalizations"]:
        name_value = row["field"]
        rule = NativeField("Normalize", name_value, row["type"], ModeValue=row["mode"], MaskValue=row["mask"])
        data, fields = native_slice(config, row, prefix, rules=(rule,))
        require(unpack("<i", data) == (row["raw"],)
                and fields == {name_value: row["projected"], name_value + "#wire": row["raw"]},
                "normalization changed the recorded signed word or projection")
        items.append({"field": name_value, "span": [row["start"][0], row["end"][0]],
                      "wire": row["raw"], "value": row["projected"], "counter": row["start"][2]})
    leaves = {}
    for row in expected["leaf_records"]:
        schema = row["layout"]
        data, fields = native_slice(config, row, prefix, schema=schema)
        observed = check_leaf(data, fields, schema, prefix)
        require(observed == row["fields"], "support layout differs from its reference fields")
        leaves[schema] = {"bytes": len(data), "counter": row["start"][2], "fields": observed}
    refused = component_refusals(prefix)
    require(not prefix.RootValue.FieldsValue, "bounded reads mutated their supporting part object")
    return {"case": name, "runtime_external_accesses": 0, "normalizations": items, "leaves": leaves,
            "config_sha256": expected["config_sha256"], "component_refusals": refused}


def branch(name, mode, mask, positive, negative):
    return NativeField("Branch", name, ModeValue=mode, MaskValue=mask,
                       BodyValue=(NativeField("Scalar", positive, "i32"),),
                       OtherValue=(NativeField("Scalar", negative, "i32"),))


def mode_rules():
    return (
        NativeField("Scalar", "selector", "i32"),
        branch("selector", "Equals", 10, "equal", "different"),
        branch("selector", "Greater", 10, "above", "not_above"),
        branch("", "NotCondition", 0x80, "clear", "masked"),
        NativeField("Normalize", "threshold", "i32", ModeValue="AtLeast", MaskValue=10),
        NativeField("Normalize", "identity", "i32", ModeValue="Identity"),
        NativeField("Normalize", "scene", "i32", ModeValue="Zero"),
        NativeField("Normalize", "atom", "u32", ModeValue="AtomState"),
        NativeField("Repeat", "fixed", ModeValue="Fixed", MaskValue=10,
                    BodyValue=(NativeField("Scalar", "value", "i32"),)),
        NativeField("Repeat", "empty", ModeValue="Fixed",
                    BodyValue=(NativeField("Scalar", "value", "i32"),)),
    )


def authored_record(selector, conditions):
    masked = bool(conditions & 0x80)
    minimum, identity, scene = {9: (-4, -78, -763), 10: (10, -3, -523), 11: (15, 9, -745)}[selector]
    atom = 0xF00000C1
    raw_rows = [i * i - 9 for i in range(10)]
    data = pack("<7iI10i", selector, 31, 47, 59, minimum, identity, scene, atom, *raw_rows)
    expected = {
        "selector": selector,
        ("equal" if selector == 10 else "different"): 31,
        ("above" if selector > 10 else "not_above"): 47,
        ("masked" if masked else "clear"): 59,
        "threshold#wire": minimum, "threshold": {9: 10, 10: 10, 11: 15}[selector],
        "identity#wire": identity, "identity": identity,
        "scene#wire": scene, "scene": 0,
        "atom#wire": atom, "atom": atom if masked else 0,
        "fixed": [{"value": value} for value in raw_rows],
        "empty": [],
    }
    fields = read_exact(data, ArchiveNode(PART, {}), ArchiveMaps(1), rules=mode_rules(), conditions=conditions)
    require(fields == expected, "authored branches or normalization used the wrong fields")
    return {"conditions": conditions, "bytes": len(data), "sha256": digest(data), "fields": fields}


def refuse(label, payload, reason, *, rules=(), schema=None):
    try:
        read_exact(payload, ArchiveNode(PART, {}), ArchiveMaps(1), rules=rules, schema=schema)
    except ValueError as error:
        require(reason in str(error), f"{label} failed at a different boundary: {error}")
        return label
    raise ValueError(f"{label} crossed the selected field scope")


def authored_case():
    guard_runtime()
    contrasting = [authored_record(9, 0), authored_record(10, 0x20), authored_record(11, 0xA0)]
    scalar = NativeField("Scalar", "value", "i32")

    def repeat(count):
        return NativeField("Repeat", "fixed", ModeValue="Fixed", MaskValue=count, BodyValue=(scalar,))

    faults = [
        refuse("branch", b"", "unsupported native branch rule", rules=(NativeField("Branch", "", ModeValue="Expression"),)),
        refuse("fixed_negative", b"", "implausible SOLIDWORKS body repeat", rules=(repeat(-1),)),
        refuse("fixed_limit", b"", "implausible SOLIDWORKS body repeat", rules=(repeat(10_000_001),)),
        refuse("fixed_truncated", pack("<i", 4) + b"\0", "truncated SOLIDWORKS archive field", rules=(repeat(2),)),
        refuse("normalization", pack("<i", 4), "unsupported native normalization rule",
               rules=(NativeField("Normalize", "value", "i32", ModeValue="Unmapped"),)),
        refuse("signed_width", pack("<I", 4), "requires an i32 word",
               rules=(NativeField("Normalize", "value", "u32", ModeValue="AtLeast"),)),
        refuse("direct_owner", b"", "unsupported SOLIDWORKS native field path f1018 without its enclosing part",
               rules=(NativeField("DirectNode", "f1018", "moSheetMetalMaster_c"),)),
        refuse("component_owner", pack("<H", 2), "unresolved archive object reference 2", schema="moComponent_c"),
    ]
    return {"case": "authored", "runtime_external_accesses": 0, "records": contrasting, "refusals": faults}


def main():
    parser = ArgumentParser(description="Verify bounded native field modes and support layouts")
    parser.add_argument("case", choices=("ladder", "concave", "circle", "authored"))
    parser.add_argument("--disclosed-root", type=Path)
    parser.add_argument("--native-witnesses", action="store_true")
    args = parser.parse_args()
    if args.case == "circle" and args.disclosed_root is None:
        parser.error("circle requires its disclosed original root")
    if args.case == "authored" and args.native_witnesses:
        parser.error("native witnesses require a disclosed original part")
    outcome = authored_case() if args.case == "authored" else native_case(
        args.case, args.disclosed_root if args.case == "circle" else ROOT,
        witness_only=args.native_witnesses
    )
    print(json.dumps(outcome, sort_keys=True))


if __name__ == "__main__":
    main()
