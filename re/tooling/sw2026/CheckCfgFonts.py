from argparse import ArgumentParser
from codecs import lookup
from functools import partial
import json
from pathlib import Path
from subprocess import check_output
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from CheckCfgMembers import digest, require
from CheckCfgOwners import audit_run
from ReadWireCfgFont import FONT, WIDTH, author_records, malformed_records, read_reference
from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.FontFields import KFontFields
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.FormatAnnotationFields import (
    KFormatAnnotationFields,
)
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadFieldsMut import ReadFieldsMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadSchemaMut import ReadSchemaMut
from convert.adapters.solidworks.Archive.Config.Link.ReadPartStart import ReadPartStart
from convert.adapters.solidworks.Archive.Header.HeaderRefNodes import HeaderRefNodes
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Container.Container import SldprtArchive

MANIFEST = ROOT / "re/solidworks/measurements/2026/ConfigFontSource01.json"
LAYOUTS = {**KFontFields, **KFormatAnnotationFields}
CONFIG_FIELDS = "src/convert/adapters/solidworks/Archive/Bodies/Layouts/Config"
PRODUCTION = (f"{CONFIG_FIELDS}/FontFields.py", f"{CONFIG_FIELDS}/FormatAnnotationFields.py")
TOOLS = ("CheckCfgFonts.py", "ReadWireCfgFont.py", "TraceCfgFont.py", "CheckCfgMembers.py", "CheckCfgOwners.py")


def describe(node):
    return [node.ClassValue.NameValue, node.ClassValue.SchemaValue, node.IndexValue]


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def read_record(data, start, layout, prefix, counter, version, conditions, diagnostic=None):
    entries = prefix.MapValue.EntriesValue
    maps = ArchiveMaps(prefix.BaseValue, prefix.MapValue)
    maps.CounterValue = counter
    context = BodyContext(version, LAYOUTS, {}, {}, FlagsValue={"conditions": conditions})
    cursor = BinaryReader(data, start)
    reader = GraphReader(cursor, maps, partial(ReadBodyMut, context))
    fields = {}
    frame = ReadFrame(context, reader, FieldScope(fields), prefix.RootValue, ReadSchemaMut, ReadFieldsMut)
    error_text = None
    try:
        ReadSchemaMut(frame, layout)
        if cursor.GetRemaining():
            raise ValueError("bounded formatting record has trailing data")
        require(diagnostic is None, f"{layout} accepted its malformed input")
    except ValueError as error:
        error_text = str(error)
        if diagnostic is None or diagnostic not in error_text:
            raise
        if version != 19000 or layout not in LAYOUTS:
            require(cursor.GetOffset() == start and not context.UsageValue.FieldCalls and not fields,
                    "unsupported formatting proceeded to wire fields")
    finally:
        actual = maps.Snapshot()
        require(maps.BaseValue == prefix.BaseValue == 4 and actual.CounterValue == counter
                and len(entries) == len(actual.EntriesValue)
                and all(left is right for left, right in zip(entries, actual.EntriesValue, strict=True))
                and not context.UsageValue.SchemaPath and not context.UsageValue.FieldPath,
                "formatting must preserve its anchored map and unwind its field scopes")
        require(not prefix.RootValue.FieldsValue, "inline formatting modified its part owner")
    return fields, dict(context.UsageValue.SchemaCalls), cursor.GetOffset(), error_text


def native_records(case, source, config, prefix, version):
    alias, = HeaderRefNodes(prefix.HeaderValue, version)
    entries = prefix.MapValue.EntriesValue
    require([entry.IndexValue for entry in entries] == [1, 2, 3] and entries[1].EntryValue is prefix.RootValue
            and entries[0].EntryValue is prefix.RootValue.ClassValue and entries[2].EntryValue is alias,
            "the live class and header aliases do not match the part start")
    reports = {}
    for layout, record in case["records"].items():
        start, end = record["interval"]
        wire = config[start:end]
        counter = record["map_counter"]
        require(len(wire) == end - start and digest(wire) == record["wire_sha256"],
                "the exact native formatting slice moved")
        require(record["map_base"] == prefix.BaseValue and record["native_map_slot_range"] == [1, counter]
                and describe(prefix.RootValue) == record["part"] and describe(alias) == record["header_alias"]
                and "fae0" in record["owner_fields"],
                "the native formatting slice no longer belongs to this part")
        fields, calls, offset, error = read_record(
            config[:end], start, layout, prefix, counter, version, record["conditions"])
        expected = read_reference(wire, layout)
        require(error is None and offset == end and canonical(fields) == canonical(expected),
                "production and independent formatting reads disagree")
        expected_calls = {layout: 1, WIDTH: 1} if layout == FONT else {layout: 1}
        require(calls == expected_calls, "unexpected formatting dispatch")
        reports[layout] = {
            "interval": [start, offset], "bytes": len(wire), "wire_sha256": digest(wire),
            "fields": fields, "fields_sha256": digest(canonical(fields).encode("ascii")),
            "map_base": prefix.BaseValue, "map_counter": counter, "layouts": calls,
        }
    require(digest(source) == case["source_sha256"], "native source changed")
    require(reports[FONT]["fields"]["f10"] == reports[WIDTH]["fields"],
            "line font and its separately framed width differ")
    return {"records": reports, "part": describe(prefix.RootValue), "header_alias": describe(alias),
            "source_sha256": case["source_sha256"], "config_sha256": case["config_sha256"],
            "model_header_sha256": case["model_header_sha256"], "anchor_slots": [1, 2, 3]}


def authored_records(prefix):
    records = author_records()
    report = {}
    counter = 62
    for layout, (wire, expected) in records.items():
        fields, calls, offset, error = read_record(wire, 0, layout, prefix, counter, 19000, 0)
        require(error is None and offset == len(wire)
                and canonical(fields) == canonical(read_reference(wire, layout)) == canonical(expected),
                "a varied formatting value or field order differs")
        report[layout] = {"bytes": len(wire), "wire_sha256": digest(wire),
                          "fields": fields, "layouts": calls}
    refusals = []
    for label, layout, wire, version, reason in malformed_records(records):
        _, _, offset, error = read_record(wire, 0, layout, prefix, counter, version, 0, reason)
        require(error is not None, "invalid formatting data was accepted")
        refusals.append({"case": label, "offset": offset, "diagnostic": error})
    return {"records": report, "refusals": refusals, "map_base": prefix.BaseValue, "map_counter": counter}


def measure():
    files = {path: digest((ROOT / path).read_bytes()) for path in PRODUCTION}
    jobs = {path: digest((HERE.parent / path).read_bytes()) for path in TOOLS}
    reports = [json.loads(check_output((sys.executable, "-I", "-B", str(HERE), name)))
               for name in ("ladder", "concave", "wire")]
    print(json.dumps({
        "archive_version": 19000, "format_version": 4,
        "compared_production_base": "b7206312cbdd4ef7b0966263e08ec84bb52ea0df",
        "source_receipt_sha256": digest(MANIFEST.read_bytes()),
        "production_sha256": files,
        "production_manifest_sha256": digest(canonical(files).encode("ascii")),
        "tool_sha256": jobs, "fresh_guarded_processes": len(reports), "results": reports,
        "native_launches": 0, "complete_config_admission": False,
    }, indent=2, sort_keys=True, allow_nan=False))


def main():
    parser = ArgumentParser()
    parser.add_argument("case", choices=("ladder", "concave", "wire", "measure"))
    name = parser.parse_args().case
    if name == "measure":
        measure()
        return
    evidence = json.loads(MANIFEST.read_bytes())
    case = evidence["native_controls"]["ladder" if name == "wire" else name]
    source = (ROOT / case["path"]).read_bytes()
    require(digest(source) == case["source_sha256"], "tracked part SHA differs")
    for codec in ("ascii", "latin-1", "cp1252", "utf-16-le"):
        lookup(codec)
    sys.addaudithook(audit_run)
    archive = SldprtArchive.from_bytes(source)
    prefix = ReadPartStart(archive)
    config = archive.Require(evidence["stream"])
    header = archive.Require(evidence["model_header"])
    require(digest(config) == case["config_sha256"] and digest(header) == case["model_header_sha256"],
            "tracked native streams differ")
    report = authored_records(prefix) if name == "wire" else native_records(
        case, source, config, prefix, evidence["archive_version"])
    report.update(case=name, runtime_external_accesses=0)
    print(canonical(report))


if __name__ == "__main__":
    main()
