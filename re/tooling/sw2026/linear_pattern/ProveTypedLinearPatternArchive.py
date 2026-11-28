from argparse import ArgumentParser
from collections import Counter
from math import dist, ulp
from pathlib import Path
from subprocess import check_output
from types import SimpleNamespace
import json
import sys


HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from AuditLinearPatternArchive import CFG, LABELS, PIN, RESOLVED, ROOT, SOURCE_PHASES, VERSION
from AuditLinearPatternArchive import checked, digest, pattern_proof, require
from Core import Obj
from convert import open_document
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


BASE = "8219597dffd297e654b33647efaadffedde7c1e3"
LOCK_REVISION = "c533e1997bf4ff1212ad0e9bc28d87368796e0a9"
LOCK_SHA256 = "feae81f34fb0505753eebad0ab11588b6a18b5fdf72f6b4c5b9ad899084f1112"
MEASUREMENTS = ROOT / "re/solidworks/measurements/2026"
DISCLOSURE_SHA256 = "07ac98da888fd8c2a7caaa0a513b73d9b81a33c2f522f51b0ed8e6dcf6c6bf63"
PATTERN_LAYOUT = "src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved"
BODY = "src/convert/adapters/solidworks/Archive/Bodies"
SOURCE_FILES = (
    *(f"{BODY}/{name}.py" for name in ("CheckPacked", "CheckPatDatum", "ValidateFields")),
    *(f"{PATTERN_LAYOUT}/{name}.py" for name in (
        "AnchorFields", "PatternBaseFields", "PatternDatumFields", "PatternDimFields", "PatternLayouts",
        "PatternOrigFields", "PatternShapeFields", "PatternTailFields",
        "ResolvedLayouts", "ResolvedSchemas", "ResolvedVirtuals",
    )),
)
CONTROLS = (
    ("ladder/L1_boss.SLDPRT",
     "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6",
     "33a190c0632c1cfb61a493671d5811c9ea3e9f81a4233adf801d28a8780af525", None),
    ("principal-revolve-discovery/PrincipalRevolveTopForward.SLDPRT",
     "4bf2c202be9ae4fc7786e50a92c4f83dc17ea4bc80492b7173075d74f678d3f0",
     "8ae01dea66fda2c0058ad4b5f82d797b90447e81a0d64387a5e68b8e83becd26", "moCompSketchEntHandle_c"),
)


def git(*args):
    return check_output(("git", *args), cwd=ROOT)


def replay(graph, config):
    return WriteResolMut(graph.RootsValue, graph.ExtraFields, VERSION, config.MapValue, graph.ContextValue)


def verify_link(archive):
    link = ReadNativeLink(archive, 0)
    config = link.ConfigValue
    graph = link.ResolvedValue
    cfg = WriteConfigMut(config.RootValue, VERSION, config.HeaderValue)[0]
    resolved, output = replay(graph, config)
    require(cfg == archive.require(CFG) and resolved == archive.require(RESOLVED),
            "production linked Config/Resolved bytes differ")
    require(graph.ReportValue["completed"] == output.ReportValue["completed"] is True
            and graph.ReportValue["missing_schemas"] == output.ReportValue["missing_schemas"] == ()
            and graph.ReportValue["provisional_schemas"] == output.ReportValue["provisional_schemas"] == ()
            and graph.MapValue == output.MapValue, "typed coverage or concrete linked map differs")
    return link, output


def packed_arrays(report):
    rows = report["native_byte_fields"]
    require(len(rows) == 8 and Counter(row["object_class"] for row in rows) ==
            {"moDisplayDim_c": 2, "moDisplayDistanceDim_c": 6}, "unexpected display-array owners")
    require(all(row["completed"] and row["schema"] == "dm.FUN_4bd03960" and row["field"] == "data"
                and row["element_type"] == "f64" and row["element_count"] == len(row["typed_values"]) == 1
                and row["length_rule"] == "count_times_native_binary64_width"
                and row["observed_length"] == row["declared_length"] == 8
                for row in rows), "untyped or incomplete display-array member")
    return [(row["object_class"], row["typed_values"][0]) for row in rows]


def make_node(runtime_class):
    return Obj(runtime_class.NameValue, schema=runtime_class.SchemaValue)


def source_owners(archive, graph, proof, original, observation):
    header = ReadHeaderGraph(archive.require(CFG + "-ModelHeader"), VERSION)
    config = ReadConfigMut(archive.require(CFG), VERSION, header, NodeMaker=make_node)
    cmgr = ReadCmgrMut(archive.require("Contents/CMgr"), VERSION)
    resolved = ReadResolvedMut(
        archive.require(RESOLVED), VERSION, config.MapValue, MakeLinkContext(config, cmgr), NodeMaker=make_node,
    )
    owners = pattern_proof(archive, SimpleNamespace(roots=(config.RootValue,)), SimpleNamespace(roots=resolved.RootsValue),
                           observation["reopened"])
    require(json.loads(json.dumps(owners)) == original["typed_pattern_evidence"]
            and resolved.ReportValue == graph.ReportValue, "ordinary linked read changed the independently bound roles")
    displays = owners["dimensions"]
    for role in ("display", "handle", "dimension", "parameter"):
        require(len({row[role]["archive_object"] for row in displays.values()}) == len(displays),
                "display, handle, dimension or parameter aliased a different role")
    require(owners["feature"]["archive_object"] == proof.IndexValue, "factory changed the pattern allocation")
    return owners


def direction_point(pattern, config, observation, owners):
    line = pattern.FieldsValue["f1288"]
    plane = line.FieldsValue["f58"]
    component = plane.FieldsValue["f58"]
    require(component.ClassValue.NameValue == "moUnitComponent_c"
            and component.FieldsValue["owner"] is config.RootValue
            and component is not config.RootValue.FieldsValue["f990"]
            and line.FieldsValue["f60"] is None, "selected plane's independently allocated component differs")
    original = observation["reopened"]
    frame = original["plate_profile"]["model_to_sketch"]
    require(frame == [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
            and all(boss["reverse"] is False for boss in (original["plate_boss"], original["seed_boss"])),
            "box-center contrast requires these exact source axes")
    plate = original["plate_profile"]["geometry"]
    corners = [segment[end] for segment in plate for end in ("start", "end")]
    center_xy = tuple((min(values) + max(values)) / 2.0 for values in zip(*corners))
    height = max(original["plate_boss"]["depth_m"], original["seed_boss"]["depth_m"])
    center = (*center_xy, height / 2.0)
    point = owners["line_point_m"]
    projected = tuple(0.0 if axis else value for axis, value in zip(owners["axis"], center, strict=True))
    error = dist(point, projected)
    require(error <= max(map(ulp, projected)), "direction point exceeds one binary64 unit from projected box center")
    return {"line_object": line.IndexValue, "plane_ref_object": plane.IndexValue,
            "unit_component_object": component.IndexValue, "part_owner_object": config.RootValue.IndexValue,
            "config_self_component_object": config.RootValue.FieldsValue["f990"].IndexValue,
            "projected_box_center_m": projected, "stored_line_point_m": point,
            "exact_binary64": tuple(map(float.hex, point)) == tuple(map(float.hex, projected)),
            "absolute_error_m": error}


def measure_source(raw, original, observation):
    archive = SldprtArchive.from_bytes(raw)
    link, emitted = verify_link(archive)
    graph = link.ResolvedValue
    config = link.ConfigValue
    (pattern,) = (node for node in graph.RootsValue if node.ClassValue.NameValue == "moLPattern_c")
    require(graph.RootsValue[-1] is pattern and len(graph.RootsValue) == 22
            and graph.MapBase == original["sdk_prefix"]["config_counter"]
            and graph.MapValue.CounterValue == original["resolved_counter"], "root order or map allocation changed")
    owners = source_owners(archive, graph, pattern, original, observation)
    caches = packed_arrays(graph.ReportValue)
    require(caches == packed_arrays(emitted.ReportValue), "typed cache values or order changed on replay")
    lists = {name: (node.IndexValue, node.FieldsValue["n"])
             for name in ("f988", "f9d8", "f8d8", "f990") if (node := pattern.FieldsValue[name]) is not None}
    require([length for _, length in lists.values()] == [1, 0, 0, 0]
            and len({index for index, _ in lists.values()}) == len(lists), "the inherited list objects differ")
    storage = {}
    for name in owners["dimensions"]:
        payload = pattern.FieldsValue[name].FieldsValue["f5b0"]
        storage[name] = {key: payload[key] for key in ("elem", "alloc_a", "alloc_b", "n")}
        require(storage[name] == {"elem": 8, "alloc_a": 16, "alloc_b": 1, "n": 1},
                "disclosed display storage allocation changed")
    doc = open_document(raw, source_format="solidworks.sldprt", strict=True)
    (feature,) = (node for node in doc.feature_timeline if node.name == owners["feature"]["name"])
    meta = doc.metadata["solidworks.typed_resolved_semantics"]
    require(meta["diagnostic"] == "multiple operation histories are outside typed blind topology"
            and meta["status"] == "unsupported" and meta["public_writer_qualified"] is False
            and len(doc.bodies) == len(doc.brep.bodies) == 1
            and type(feature.definition).__name__ == "NativeFeatureDefinition",
            "generic public pattern behavior changed")
    return {
        "name": original["name"], "source_sha256": digest(raw),
        "config": {"sha256": digest(archive.require(CFG)), "bytes": len(archive.require(CFG))},
        "resolved": {"sha256": digest(archive.require(RESOLVED)), "bytes": len(archive.require(RESOLVED)),
                     "roots": len(graph.RootsValue), "base": graph.MapBase, "next_counter": graph.MapValue.CounterValue,
                     "packed_values_per_direction": caches, "opaque_bytes": 0},
        "datum": direction_point(pattern, config, observation, owners),
        "drivers": {name: (row["stored_value"], row["cached_display"]) for name, row in owners["dimensions"].items()},
        "scope": owners["scope"], "list_objects_and_counts": lists, "display_storage": storage,
        "public_typed_profile_refusal": meta["diagnostic"],
    }


def refused(link):
    graph = link.ResolvedValue
    config = link.ConfigValue
    fields = graph.RootsValue[-1].FieldsValue
    faults = (
        (fields, "f1288", None, "linear pattern direction requires its local datum chain"),
        (fields["f1288"].FieldsValue, "f58", None, "linear pattern direction requires its local datum chain"),
        (fields, "f820", fields["f988"], "linear pattern skip object"),
        (fields, "nf30", 1, "linear pattern dimension increments"),
        (fields["ffa0"], "f30", 2, "alternate linear pattern shape form"),
        (fields["f1258"].FieldsValue["f5b0"], "elem", 4,
         "packed native values require the proven ordinary display binary64 owner"),
    )
    results = []
    for values, field_name, corrupt, reason in faults:
        original = values[field_name]
        values[field_name] = corrupt
        try:
            replay(graph, config)
        except BodyUnsupported as error:
            require(str(error).endswith(reason), "wrong malformed pattern refusal")
        else:
            raise ValueError("malformed pattern body unexpectedly re-emits")
        finally:
            values[field_name] = original
        results.append({"field": field_name, "reason": reason})
    return results


def measure_controls():
    for path, native_pin, stream_pin, expected in CONTROLS:
        raw = checked(ROOT / "re/solidworks/v2026/corpus" / path, native_pin)
        archive = SldprtArchive.from_bytes(raw)
        link, _ = verify_link(archive)
        require(digest(archive.require(RESOLVED)) == stream_pin, "legacy resolved control changed")
        doc = open_document(raw, source_format="solidworks.sldprt", strict=True)
        require(len(doc.bodies) == 1 and doc.metadata["solidworks.typed_resolved_semantics"]["status"] == "supplemented",
                "legacy strict public read changed")
        if expected is not None:
            (revolve,) = (node for node in link.ResolvedValue.RootsValue if node.ClassValue.NameValue == "moRevolution_c")
            selection = revolve.FieldsValue["f830"].FieldsValue["f58"]
            require(selection.ClassValue.NameValue == expected, "legacy sketch wrapper changed")
        yield {"path": path, "source_sha256": native_pin, "resolved_sha256": stream_pin, "line_owner": expected}


def measure(packet):
    require(packet.name == "LinearPatternSourcePacket03", "use only the disclosed packet")
    disclosure = json.loads(checked(MEASUREMENTS / "LocalLinearPatternDisclosedArchive01.json", DISCLOSURE_SHA256))
    lock = json.loads(checked(packet / "Progress/disclosed-lock.json", PIN))
    require(disclosure["native_source_lock_sha256"] == PIN and disclosure["native_oracle_phases_rechecked"] == 14
            and lock["cohort"] == "disclosed" and lock["passed"] and lock["writer_output_count"] == 0
            and tuple(case["name"] for case in lock["cases"]) == LABELS, "disclosed custody differs")
    original = iter(disclosure["cases"])
    cases, refusals = [], None
    for case in lock["cases"]:
        source_dir = packet / "DisclosedNative" / case["name"]
        phases = {row["phase"]: row for row in case["phases"]}
        for pinned, phase in zip(case["native_sources"], SOURCE_PHASES, strict=True):
            row = next(original)
            require(row["name"] == pinned["name"] and row["native_sha256"] == pinned["sha256"],
                    "disclosed lock conflicts with the independent intake")
            raw = checked(source_dir / pinned["name"], pinned["sha256"], pinned["bytes"])
            record = json.loads(checked(source_dir / phase / "Record.json", phases[phase]["record_sha256"]))
            require(record["open"] == {"opened": True, "errors": 0, "warnings": 0}
                    and record["native_sha256"] == pinned["sha256"], "disclosed native measurement mismatch")
            cases.append(measure_source(raw, row, record))
            if refusals is None:
                refusals = refused(ReadNativeLink(SldprtArchive.from_bytes(raw), 0))
    require(next(original, None) is None and len(cases) == 6, "missing disclosed source")
    return cases, refusals


def main(packet, output):
    git("merge-base", "--is-ancestor", BASE, "HEAD")
    git("merge-base", "--is-ancestor", LOCK_REVISION, "HEAD")
    require(digest(git("show", LOCK_REVISION + ":re/solidworks/measurements/2026/LocalLinearPatternHeldoutSourceLock01.json"))
            == LOCK_SHA256, "pre-writer lock digest changed")
    changed = set(git("diff", "--name-only", BASE, "--", "src").decode().splitlines())
    untracked = set(git("ls-files", "--others", "--exclude-standard", "--", "src").decode().splitlines())
    require(changed | untracked == set(SOURCE_FILES), "production codec closure has unexpected paths")
    cases, refusals = measure(packet)
    controls = list(measure_controls())
    require(not any(name in ("Swapp", "pythoncom", "pywintypes") or name.startswith("win32com")
                    for name in sys.modules), "typed archive comparison imported an oracle dependency")
    closure = (*SOURCE_FILES, HERE.relative_to(ROOT).as_posix(), str(HERE.with_name("AuditLinearPatternArchive.py").relative_to(ROOT)))
    summary = {"schema": "kit.sw2026.local-linear-pattern-typed-archive.v1", "base_revision": BASE,
               "prewriter_lock_revision": LOCK_REVISION, "prewriter_lock_sha256": LOCK_SHA256,
               "disclosed_intake_sha256": DISCLOSURE_SHA256, "disclosed_native_lock_sha256": PIN,
               "file_sha256": {name: digest((ROOT / name).read_bytes()) for name in closure},
               "linked_exact_streams": 2 * (len(cases) + len(controls)), "pattern_binary64_values_per_direction": 8 * len(cases),
               "native_processes_started": 0, "native_files_written": 0, "heldout_inputs_read": 0,
               "controls": controls, "malformed_model_refusals": refusals, "cases": cases}
    receipt = (json.dumps(summary, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with output.open("xb") as stream:
        stream.write(receipt)
    print(json.dumps({"cases": len(cases), "controls": len(controls), "refusals": len(refusals),
                      "receipt_sha256": digest(receipt)}))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    main(args.packet, args.output)
