from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
from struct import pack
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.Archive.Config.Members.CfgMemberTypes import (
    KFeatColorClass,
    KRelMgrClass,
)
from convert.adapters.solidworks.Archive.Config.Members.ReadCfgMember import ReadCfgMember
from convert.adapters.solidworks.Archive.Maps.MapEntry import MapEntry
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive

CASES = {
    "ladder": (
        "ladder/L1_boss.SLDPRT",
        "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6",
        "e7e700d5b112e7d9d1b1297bac8149707e67d9aac2e3c6f890b4cb2f97b1e5b2",
        (
            (
                3182, 3232, 59,
                "fa18856e20508236ea27e49623afc36e24a874ac3cf9aba05fdb24eeb4fe6325",
            ),
            (
                24261, 24287, 95,
                "c23c2155d485734bacafdb26beb943aba5a96aad9bcc48f00af98fb6383b1421",
            ),
        ),
    ),
    "concave": (
        "local-import-readback/ConcaveOwned.SLDPRT",
        "fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33",
        "f8b42cb72d75f14be04410c18daae6f77164e2561dd5e99d7f26a107b5b049a1",
        (
            (
                2235, 2285, 52,
                "36d9b58ea98f929c99fb07af9cfe08f68b8f7138b05c7005f1e43d09231e4391",
            ),
            (
                22484, 22486, 90,
                "96a296d224f285c67bee93c30f8a309157f0daa35dc5b87e410b78630a09cfc7",
            ),
        ),
    ),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def project(value):
    if isinstance(value, CStringValue):
        return value.TextValue
    if isinstance(value, dict):
        return {name: project(field) for name, field in value.items()}
    if isinstance(value, list):
        return [project(row) for row in value]
    return value


def inspect(data, graph, seed):
    inherited = graph.MapValue.EntriesValue[: len(seed.EntriesValue)]
    require(
        len(inherited) == len(seed.EntriesValue)
        and all(a is b for a, b in zip(inherited, seed.EntriesValue)),
        "inherited member slots changed",
    )
    require(graph.ReportValue["completed"], "incomplete member record")
    node = graph.RootValue
    identity = None
    fields = None
    if node is not None:
        require(node.StartOffset == 0 and node.EndOffset == len(data), "member offsets changed")
        identity = [node.ClassValue.NameValue, node.ClassValue.SchemaValue, node.IndexValue]
        fields = project(node.FieldsValue)
    return {
        "bytes": len(data),
        "sha256": digest(data),
        "class": identity,
        "fields": fields,
        "map_counter": graph.MapValue.CounterValue,
        "inherited_slots": [entry.IndexValue for entry in inherited],
        "layouts": graph.ReportValue["used_schemas"],
        "field_calls": graph.ReportValue["field_calls"],
    }


def originals(case):
    relative, source_hash, config_hash, owners = CASES[case]
    path = ROOT / "re/solidworks/v2026/corpus" / relative
    source = path.read_bytes()
    require(digest(source) == source_hash, "wrong member control bytes")
    archive = SldprtArchive.from_bytes(source)
    version = ContainerMo(archive.streams)
    require(archive.format_version == 4 and version == 19000, "wrong member control version")
    config = archive.require("Contents/Config-0")
    require(digest(config) == config_hash, "wrong physical configuration")
    result = []
    inherited = ()
    for owner, role in zip(owners, (KRelMgrClass, KFeatColorClass), strict=True):
        start, end, counter, expected_hash = owner
        data = config[start:end]
        require(digest(data) == expected_hash, "wrong bounded native member")
        seed = MapSnapshot(counter, inherited)
        value = ReadCfgMember(data, version, seed, role)
        result.append((data, value, seed))
        inherited = value.MapValue.EntriesValue
    require(digest(path.read_bytes()) == source_hash, "source member control changed")
    return result, source_hash, config_hash


def refuse(label, data, seed, role, expected, version=19000):
    try:
        ReadCfgMember(data, version, seed, role)
    except ValueError as error:
        require(expected in str(error), f"{label} failed for a different reason: {error}")
        return label
    raise ValueError(f"{label} accepted outside the declared member scope")


def native_case(case):
    records, source_hash, config_hash = originals(case)
    native = [inspect(*row) for row in records]
    relation, color = records
    data, graph, seed = relation
    color_data, _, color_seed = color
    return {
        "case": case,
        "source_sha256": source_hash,
        "configuration_sha256": config_hash,
        "members": native,
        "refusals": [
            refuse("relation_truncated", data[:-1], seed, KRelMgrClass, "truncated"),
            refuse("color_trailing", color_data + b"\0", color_seed, KFeatColorClass, "trailing"),
            refuse("wrong_owner", data, seed, KFeatColorClass, "unsupported body owner"),
            refuse("version", color_data, color_seed, KFeatColorClass, "archive version 19000", 18900),
            refuse("null_relation", b"\0\0", seed, KRelMgrClass, "requires its concrete root"),
            refuse(
                "prior_relation_object",
                pack("<H", graph.RootValue.IndexValue),
                graph.MapValue,
                KRelMgrClass,
                "requires a new root object",
            ),
        ],
    }


def ascii_text(text):
    data = text.encode("ascii")
    return pack("<B", len(data)) + data


def author_relation(class_slot, count, rows):
    cache = pack("<H", 1) + ascii_text("relation length") + pack("<d", 1.25)
    return b"".join((
        pack("<HH", 0x8000 | class_slot, 0),
        cache,
        ascii_text("ordered members"),
        pack("<iIiiHiI", -7, 0xFEED1234, 2, -8, 0, 12, count),
        b"".join(pack("<H", row) for row in rows),
    ))


def author_color(schema, count):
    name = KFeatColorClass.NameValue.encode("ascii")
    return pack("<HHH", 0xFFFF, schema, len(name)) + name + pack("<I", count)


def authored_case():
    controls, _, _ = originals("ladder")
    _, original, _ = controls[0]
    seed = original.MapValue
    slot = seed.EntriesValue[0].IndexValue
    require(seed.EntriesValue[0].EntryValue == KRelMgrClass, "unexpected relation class seed")
    rows = (0, 0)
    data = author_relation(slot, len(rows), rows)
    graph = ReadCfgMember(data, 19000, seed, KRelMgrClass)
    color = author_color(0, 0x80000000)
    color_seed = MapSnapshot(graph.MapValue.CounterValue, graph.MapValue.EntriesValue)
    colors = ReadCfgMember(color, 19000, color_seed, KFeatColorClass)
    empty = MapSnapshot(seed.CounterValue, ())
    wrong_kind = MapSnapshot(seed.CounterValue, (MapEntry(slot, original.RootValue),))
    return {
        "case": "authored",
        "members": [inspect(data, graph, seed), inspect(color, colors, color_seed)],
        "refusals": [
            refuse("missing_class", data, empty, KRelMgrClass, "archive class reference"),
            refuse("wrong_seed_kind", data, wrong_kind, KRelMgrClass, "archive class reference"),
            refuse("truncated_repeat", data[:-1], seed, KRelMgrClass, "archive tag"),
            refuse(
                "oversized_repeat",
                author_relation(slot, 10_000_001, ()),
                seed,
                KRelMgrClass,
                "implausible SOLIDWORKS body repeat",
            ),
            refuse(
                "unqualified_relation_owner",
                author_relation(slot, 1, (original.RootValue.IndexValue,)),
                seed,
                KRelMgrClass,
                "unqualified objects",
            ),
            refuse(
                "wrong_color_schema",
                author_color(1, 0),
                color_seed,
                KFeatColorClass,
                "unsupported body owner",
            ),
            refuse(
                "unqualified_color_row",
                author_color(0, 1),
                color_seed,
                KFeatColorClass,
                "moVisualProperties_c.restore",
            ),
        ],
    }


def main():
    parser = ArgumentParser(description="Verify bounded ordinary configuration members")
    parser.add_argument("case", choices=(*CASES, "authored"))
    args = parser.parse_args()
    report = authored_case() if args.case == "authored" else native_case(args.case)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
