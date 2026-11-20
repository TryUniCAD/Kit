from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
from struct import pack
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from convert.adapters.solidworks.Archive.Config.Units.ReadUnitTable import ReadUnitTable
from convert.adapters.solidworks.Archive.Maps.MapEntry import MapEntry
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from ReadWireUnitFields import read_wire_units

CASES = {
    "ladder": (
        "ladder/L1_boss.SLDPRT",
        "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6",
        "e7e700d5b112e7d9d1b1297bac8149707e67d9aac2e3c6f890b4cb2f97b1e5b2",
        (
            (
                925, 2412, 8,
                "da33746c4a8df51f7fadda4e37b4ab8a1ab3e6040e63443fe8183d2f93f07e2c",
            ),
        ),
    ),
    "concave": (
        "local-import-readback/ConcaveOwned.SLDPRT",
        "fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33",
        "f8b42cb72d75f14be04410c18daae6f77164e2561dd5e99d7f26a107b5b049a1",
        (
            (
                278, 1699, 8,
                "1faed4f6924ec416c0afe46260f545861861ae7a893063344d0254affe0723f3",
            ),
            (
                19392, 20447, 60,
                "99cf5c6a939a6ffeb70775bb0eec9ef24230331e73c1f186d4673a32248af14e",
            ),
        ),
    ),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(payload):
    return sha256(payload).hexdigest()


def unit_rows(graph):
    return tuple(row["o"] for row in graph.RootValue.FieldsValue["items"])


def unit_projection(value):
    if isinstance(value, ArchiveNode):
        return (
            value.ClassValue.NameValue,
            value.ClassValue.SchemaValue,
            value.IndexValue,
            value.StartOffset,
            value.EndOffset,
            unit_projection(value.FieldsValue),
        )
    if isinstance(value, dict):
        return {name: unit_projection(field) for name, field in value.items()}
    if isinstance(value, list):
        return [unit_projection(field) for field in value]
    return value


def compare_wire(data, seed, graph, classes):
    reference, counter, wire_classes = read_wire_units(data, seed.CounterValue, classes)
    observed = unit_projection(graph.RootValue)
    canonical = json.dumps(reference, sort_keys=True, allow_nan=False, separators=(",", ":"))
    require(
        json.dumps(observed, sort_keys=True, allow_nan=False, separators=(",", ":"))
        == canonical,
        "typed unit values differ from the independent native field projection",
    )
    require(graph.MapValue.CounterValue == counter, "unit reference counter differs")
    require(
        {
            entry.IndexValue: (entry.EntryValue.NameValue, entry.EntryValue.SchemaValue)
            for entry in graph.MapValue.EntriesValue
            if isinstance(entry.EntryValue, RuntimeClass)
        } == wire_classes,
        "unit reference class identities differ",
    )
    return digest(canonical.encode()), wire_classes


def inspect(graph, seed, fields_hash):
    units = unit_rows(graph)
    length = units[0]
    override = length.FieldsValue["fb8"]
    require(
        all(
            old is new
            for old, new in zip(seed.EntriesValue, graph.MapValue.EntriesValue)
        )
        and len(graph.MapValue.EntriesValue) >= len(seed.EntriesValue),
        "unit decode changed an inherited entry",
    )
    require(graph.ReportValue["completed"], "incomplete typed unit table")
    return {
        "bytes": graph.RootValue.EndOffset,
        "rows": len(units),
        "root_index": graph.RootValue.IndexValue,
        "next_index": graph.MapValue.CounterValue,
        "shared_classes": len(seed.EntriesValue),
        "schema_count": len(graph.ReportValue["used_schemas"]),
        "field_projection_sha256": fields_hash,
        "length": (
            length.FieldsValue["f0c"],
            length.FieldsValue["f18"],
            length.FieldsValue["fb0"],
        ),
        "length_override_index": None if override is None else override.IndexValue,
        "angle": units[1].FieldsValue["fb0"],
        "density_override": units[3].FieldsValue["has_fb8"],
        "system": units[6].FieldsValue["fb0"],
    }


def refuse(label, data, seed, expected, version=19000):
    try:
        ReadUnitTable(data, version, seed)
    except ValueError as error:
        require(expected in str(error), f"{label} failed for a different reason: {error}")
        return label
    raise ValueError(f"{label} accepted outside the scoped native unit table")


def first_refusals(data, seed, graph):
    units = unit_rows(graph)
    density = units[3]
    last = units[-1]
    presence = density.EndOffset - 7
    require(data[presence] == 0, "fixture no longer has the ordinary density flag")
    return (
        refuse("truncated", data[:-1], seed, "truncated SOLIDWORKS archive field"),
        refuse("trailing", data + b"\0", seed, "trailing data"),
        refuse("version", data, seed, "requires archive version 19000", 18900),
        refuse(
            "density_override",
            data[:presence] + b"\x01\0\0" + data[presence + 1 :],
            seed,
            "unsupported density override",
        ),
        refuse(
            "earlier_root",
            pack("<H", graph.RootValue.IndexValue),
            graph.MapValue,
            "requires a new root object",
        ),
        refuse(
            "null_row",
            data[: last.StartOffset] + b"\0\0" + data[last.EndOffset :],
            seed,
            "unsupported row owners",
        ),
    )


def linked_seed(graph, counter):
    entries = tuple(
        entry
        for entry in graph.MapValue.EntriesValue
        if isinstance(entry.EntryValue, RuntimeClass)
    )
    return MapSnapshot(counter, entries)


def later_refusals(data, seed, graph):
    descriptor = seed.EntriesValue[0]
    require(descriptor.EntryValue == graph.RootValue.ClassValue, "wrong root test slot")
    wrong_kind = MapSnapshot(
        seed.CounterValue, (MapEntry(descriptor.IndexValue, graph.RootValue),)
    )
    return (
        refuse(
            "absent_class_seed",
            data,
            MapSnapshot(seed.CounterValue, ()),
            "unresolved or wrong kind archive class reference",
        ),
        refuse(
            "wrong_seed_kind",
            data,
            wrong_kind,
            "unresolved or wrong kind archive class reference",
        ),
    )


def observe(case_name):
    relative, source_hash, config_hash, tables = CASES[case_name]
    path = ROOT / "re/solidworks/v2026/corpus" / relative
    source = path.read_bytes()
    require(digest(source) == source_hash, "unexpected native control bytes")
    archive = SldprtArchive.from_bytes(source)
    version = ContainerMo(archive.streams)
    require(archive.format_version == 4 and version == 19000, "unsupported native control")
    config = archive.require("Contents/Config-0")
    require(digest(config) == config_hash, "unexpected native configuration")
    start, end, base, table_hash = tables[0]
    data = config[start:end]
    require(digest(data) == table_hash, "unexpected first unit table")
    seed = MapSnapshot(base, ())
    first = ReadUnitTable(data, version, seed)
    fields_hash, classes = compare_wire(data, seed, first, {})
    seen = [inspect(first, seed, fields_hash)]
    refused = list(first_refusals(data, seed, first))
    if len(tables) == 1:
        override = unit_rows(first)[0].FieldsValue["fb8"]
        require(override is not None, "native length override vanished")
        refused.append(
            refuse("wrong_map_base", data, MapSnapshot(1, ()), "archive class reference")
        )
        refused.append(
            refuse(
                "wrong_length_owner",
                data[: override.StartOffset]
                + pack("<H", first.RootValue.IndexValue)
                + data[override.EndOffset :],
                seed,
                "wrong length override",
            )
        )
    else:
        start, end, base, table_hash = tables[1]
        data = config[start:end]
        require(digest(data) == table_hash, "unexpected linked unit table")
        seed = linked_seed(first, base)
        second = ReadUnitTable(data, version, seed)
        fields_hash, _ = compare_wire(data, seed, second, classes)
        seen.append(inspect(second, seed, fields_hash))
        refused.extend(later_refusals(data, seed, first))
    require(digest(path.read_bytes()) == source_hash, "native input changed")
    return {
        "case": case_name,
        "archive_version": version,
        "source_sha256": source_hash,
        "configuration_sha256": config_hash,
        "tables": seen,
        "refusals": refused,
    }


def main():
    parser = ArgumentParser(description="Verify native version-19000 unit table records")
    parser.add_argument("case", choices=CASES)
    arguments = parser.parse_args()
    print(json.dumps(observe(arguments.case), sort_keys=True))


if __name__ == "__main__":
    main()
