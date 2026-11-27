from argparse import ArgumentParser
from codecs import lookup
from functools import partial
import json
from pathlib import Path
from subprocess import check_output
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))

from CheckCfgFonts import canonical, describe, digest, require, audit_run
from ReadWireCfgLabel import LABELS, BASE, SUFFIXES, authored_controls, malformed_controls, read_label_reference
from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.FormatAnnotationFields import KFormatAnnotationFields
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.LabelAnnotationFields import KLabelAnnotationFields
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.MaterialFields import KMaterialFields
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

MANIFEST = ROOT / "re/solidworks/measurements/2026/ConfigLabelSource01.json"
LAYOUTS = {**KFormatAnnotationFields, **KMaterialFields, **KLabelAnnotationFields}
CONFIG = "src/convert/adapters/solidworks/Archive/Bodies"
PRODUCTION = (f"{CONFIG}/IsBranchTaken.py", *(f"{CONFIG}/Layouts/Config/{name}.py" for name in
              ("LabelAnnotationFields", "ViewLabelFields", "MaterialFields", "FormatAnnotationFields")))
TOOLS = ("CheckCfgLabels", "ReadWireCfgLabel", "TraceCfgLabels", "CheckCfgFonts", "ReadWireCfgFont",
         "TraceCfgFont", "CheckCfgOwners", "CheckCfgMembers")


def read_labels(data, start, prefix, counter, conditions, version=19000, refusal=None):
    entries = prefix.MapValue.EntriesValue
    maps = ArchiveMaps(prefix.BaseValue, prefix.MapValue)
    maps.CounterValue = counter
    context = BodyContext(version, LAYOUTS, {}, {}, FlagsValue={"conditions": conditions})
    cursor = BinaryReader(data, start)
    reader = GraphReader(cursor, maps, partial(ReadBodyMut, context))
    fields, intervals = {}, {}

    def observe(frame, layout):
        before = cursor.GetOffset()
        ReadSchemaMut(frame, layout)
        if layout in KLabelAnnotationFields:
            intervals.setdefault(layout, []).append([before, cursor.GetOffset()])

    frame = ReadFrame(context, reader, FieldScope(fields), prefix.RootValue, observe, ReadFieldsMut)
    found = None
    try:
        observe(frame, LABELS)
        if cursor.GetRemaining() != 0:
            raise ValueError("bounded label definitions have trailing data")
    except ValueError as error:
        found = str(error)
        if refusal is None or refusal not in found:
            raise
    finally:
        after = maps.Snapshot()
        require(maps.BaseValue == prefix.BaseValue == 4 and after.CounterValue == counter
                and len(after.EntriesValue) == len(entries)
                and all(left is right for left, right in zip(entries, after.EntriesValue, strict=True))
                and not context.UsageValue.SchemaPath and not context.UsageValue.FieldPath
                and not prefix.RootValue.FieldsValue and not context.PendingNodes
                and "Node" not in context.UsageValue.FieldCalls,
                "view label decoding changed its map or executed an unqualified object")
    require((found is None) == (refusal is None), "unexpected label admission")
    return {
        "fields": fields, "offset": cursor.GetOffset(), "intervals": intervals,
        "schema_calls": dict(context.UsageValue.SchemaCalls),
        "field_calls": dict(context.UsageValue.FieldCalls), "diagnostic": found,
    }


def verify_group(data, start, end, prefix, counter, conditions):
    decoded = read_labels(data[:end], start, prefix, counter, conditions)
    expected, children = read_label_reference(data[start:end], conditions)
    intervals = decoded["intervals"]
    require(decoded["offset"] == end and intervals[LABELS] == [[start, end]]
            and canonical(decoded["fields"]) == canonical(expected),
            "the planner and independent label fields differ")
    for layout, child_start, base_end, child_end in children:
        require(intervals[layout] == [[start + child_start, start + child_end]],
                "a concrete label changed its native boundary")
    bases = [[start + child_start, start + base_end] for _, child_start, base_end, _ in children]
    require(intervals[BASE] == bases, "shared label base consumed its concrete suffix")
    return decoded, children


def native_case(control, data, prefix):
    label = control["labels"]
    alias, = HeaderRefNodes(prefix.HeaderValue, 19000)
    anchors = prefix.MapValue.EntriesValue
    require([entry.IndexValue for entry in anchors] == label["anchor_slots"]
            and anchors[0].EntryValue is prefix.RootValue.ClassValue
            and anchors[1].EntryValue is prefix.RootValue and anchors[2].EntryValue is alias
            and describe(prefix.RootValue) == label["part"] and describe(alias) == label["header_alias"]
            and label["map_base"] == 4 and label["native_map_entries"] == label["map_counter"] - 1
            and label["owner_fields"][-2:] == ["fae0", "f2750"],
            "the tracked label group does not match the physical part and header")
    start, end = label["interval"]
    result, children = verify_group(data, start, end, prefix, label["map_counter"], label["conditions"])
    require(digest(data[start:end]) == label["wire_sha256"] and result["schema_calls"] == control["layout_calls"],
            "the group no longer correlates with the pinned native source")
    for (layout, child_start, base_end, child_end), base, child, (key, _, _, _) in zip(
            children, control["bases"], control["children"], SUFFIXES, strict=True):
        require(child["layout"] == layout and child["interval"] == [start + child_start, start + child_end]
                and base["interval"] == [start + child_start, start + base_end]
                and child["owner_fields"][-1:] == [key] and base["owner_fields"][-2:] == [key, BASE]
                and digest(data[slice(*child["interval"])]) == child["wire_sha256"]
                and digest(data[slice(*base["interval"])]) == base["wire_sha256"]
                and result["fields"][key]["f48"] == base["f48"] == -1
                and not base["f50_present"] and "f50" not in result["fields"][key],
                "a concrete label left its measured direct owner")
    return {"case_scope": "tracked_native_part", "root_interval": [start, end],
            "map_base": 4, "map_counter": label["map_counter"], "anchor_slots": label["anchor_slots"],
            "part": label["part"], "header_alias": label["header_alias"],
            "schema_calls": result["schema_calls"], "field_calls": result["field_calls"],
            "field_sha256": digest(canonical(result["fields"]).encode("ascii")),
            "body_sha256": label["wire_sha256"], "source_sha256": control["source_sha256"],
            "intervals": result["intervals"],
            "selectors": [result["fields"][key]["f48"] for key, _, _, _ in SUFFIXES]}


def authored_case(prefix, counter):
    good = []
    for name, data, conditions in authored_controls():
        result, _ = verify_group(data, 0, len(data), prefix, counter, conditions)
        good.append({
            "case": name, "conditions": conditions, "bytes": len(data),
            "sha256": digest(data), "field_sha256": digest(canonical(result["fields"]).encode("ascii")),
            "selectors": [result["fields"][key]["f48"] for key, _, _, _ in SUFFIXES],
            "first_label": result["fields"]["f18"], "section_suffix": result["fields"]["fe8"]["fec"],
            "branch_calls": result["field_calls"]["Branch"],
        })
    _, data, conditions = authored_controls()[0]
    _, children = read_label_reference(data, conditions)
    refused = []
    for name, data, conditions, version, reason, cursor in malformed_controls(data, children):
        result = read_labels(data, 0, prefix, counter, conditions, version, reason)
        require(result["offset"] == cursor, f"{name} had the wrong refusal offset")
        before_reads = result["field_calls"]
        if "layer" in name or name == "active_zero_selector":
            require(before_reads == {"Scalar": 14, "Embed": 1, "Base": 1, "Branch": 2, "Fail": 1}
                    and "f18" not in result["fields"],
                    "conditional layer handling advanced past its signed selector")
        if name == "wrong_archive_version":
            require(not before_reads and not result["fields"], "archive version check read fields")
        refused.append({"case": name, "offset": cursor, "diagnostic": result["diagnostic"]})
    return {"positives": good, "refusals": refused, "map_base": 4, "map_counter": counter,
            "conditional_layer_admitted": False}


def measure():
    paths = {path: digest((ROOT / path).read_bytes()) for path in PRODUCTION}
    tools = {f"{name}.py": digest((HERE.parent / f"{name}.py").read_bytes()) for name in TOOLS}
    reports = [json.loads(check_output((sys.executable, "-I", "-B", str(HERE), case)))
               for case in ("ladder", "concave", "wire")]
    print(json.dumps({
        "base": "f3d8760f214d65fbe71aa4b8bf81a17f553dbb60", "format_version": 4, "archive_version": 19000,
        "source_receipt_sha256": digest(MANIFEST.read_bytes()), "production_sha256": paths,
        "production_manifest_sha256": digest(canonical(paths).encode("ascii")), "tool_sha256": tools,
        "guarded_fresh_processes": len(reports), "native_launches": 0, "complete_config_admission": False,
        "results": reports,
    }, indent=2, sort_keys=True, allow_nan=False))


def main():
    parser = ArgumentParser()
    parser.add_argument("case", choices=("ladder", "concave", "wire", "measure"))
    case = parser.parse_args().case
    if case == "measure":
        measure()
        return
    evidence = json.loads(MANIFEST.read_bytes())
    control = evidence["native_controls"]["ladder" if case == "wire" else case]
    source = (ROOT / control["path"]).read_bytes()
    require(digest(source) == control["source_sha256"], "the tracked source changed")
    for codec in ("ascii", "latin-1", "cp1252", "utf-16-le"):
        lookup(codec)
    sys.addaudithook(audit_run)
    archive = SldprtArchive.from_bytes(source)
    prefix = ReadPartStart(archive)
    data = archive.Require("Contents/Config-0")
    header = archive.Require("Contents/Config-0-ModelHeader")
    require(digest(data) == control["config_sha256"] and digest(header) == control["header_sha256"],
            "the tracked streams changed")
    result = authored_case(prefix, control["labels"]["map_counter"]) if case == "wire" else native_case(
        control, data, prefix)
    result.update(case=case, runtime_external_accesses=0)
    print(canonical(result))


if __name__ == "__main__":
    main()
