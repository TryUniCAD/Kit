from argparse import ArgumentParser
from collections import Counter
from functools import partial
from hashlib import sha256
from pathlib import Path
from struct import unpack
from subprocess import check_output
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
TOOLS = HERE.parents[1]
sys.path[:0] = [str(ROOT / "src"), str(TOOLS), str(TOOLS / "serial")]

from AuditArchiveCorpus import compact_stream, sdk_definition, sdk_stream
from Core import Obj
from RoundTrip import PLANS, REQUIRED, expand, registry, stream_roundtrip
from defs.ConfigPart import load_config
from defs.ResolvedCore import load_resolved
from convert import open_document
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Counts.ReadCount import ReadCount
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Resolved.MakeResolvedCtx import MakeResolvedCtx
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


REVISION = "5664d55335d9af2403f60ffe1f59ee0e8aba89bc"
PIN = "8239fc92779aadd6a0116ad2df9e7969568394a301e1ed11aa44fc3875ac0426"
VERSION = 19000
CFG = "Contents/Config-0"
RESOLVED = CFG + "-ResolvedFeatures"
SOURCE_PHASES = ("pristine-reopen", "spacing-reopen", "instances-reopen")
ALL_PHASES = ("author", "pristine-reopen", "spacing-edit", "spacing-reopen", "instances-edit", "instances-reopen")
LABELS = ("D01X", "D02Y")
MISSING = "unsupported SOLIDWORKS body class moLPattern_c schema 1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def checked(path, pin, count=None):
    require(path.is_file() and not path.is_symlink(), "disclosed evidence is missing")
    raw = path.read_bytes()
    require(digest(raw) == pin and (count is None or len(raw) == count), "disclosed evidence digest differs")
    return raw


def node_name(node):
    value = node.get("f18")
    return value.get("f08") if isinstance(value, Obj) else None


def node_id(node):
    return {"class": node.cls, "archive_object": node.index, "name": node_name(node)}


def vector(value):
    return tuple(value[key] for key in "xyz")


def sdk_prefix(archive):
    header = ReadHeaderGraph(archive.require(CFG + "-ModelHeader"), VERSION)
    cfg = ReadConfigMut(archive.require(CFG), VERSION, header)
    require(archive.require(CFG) == WriteConfigMut(cfg.RootValue, VERSION, header)[0],
            "production Config-0 did not re-emit exactly")
    cmgr = ReadCmgrMut(archive.require("Contents/CMgr"), VERSION)
    context = MakeResolvedCtx(VERSION, cfg.MapValue, MakeLinkContext(cfg, cmgr), None)
    cursor = BinaryReader(archive.require(RESOLVED))
    base = cursor.ReadUnsigned(4)
    roots, cursor.OffsetValue = ReadCount(cursor.BytesValue, cursor.OffsetValue)
    require(base == cfg.MapValue.CounterValue and roots == 22, "production resolved prefix differs")
    graph = GraphReader(cursor, ArchiveMaps(base, cfg.MapValue), partial(ReadBodyMut, context))
    accepted = []
    for index in range(roots):
        at = cursor.OffsetValue
        try:
            owner = ReadNodeMut(graph)
        except BodyUnsupported as error:
            require(str(error) == MISSING and index == roots - 1, "unexpected production reader boundary")
            break
        accepted.append(owner.ClassValue.NameValue)
    else:
        raise ValueError("production reader unexpectedly admitted the pattern")
    try:
        ReadNativeLink(archive, 0)
    except BodyUnsupported as error:
        require(str(error) == MISSING, "normal linked reader reached a different barrier")
    else:
        raise ValueError("normal linked reader unexpectedly admitted the pattern")
    return {"root_ordinal": index, "previous_roots": len(accepted), "class_tag_offset": at,
            "body_offset": cursor.OffsetValue, "reason": MISSING, "config_counter": base, "resolved_root_count": roots}


def display_value(pattern, key):
    display = pattern[key]
    array = display["f5b0"]
    (handle,) = tuple(row["o"] for row in display["f850"])
    dimension = handle["ff0"]
    parameter = dimension["f28"]
    require(display["n850"] == array["n"] == 1 and handle.cls == "moFeatureDimHandle_c"
            and array["elem"] == len(array["data"]) == 8, "display value is not its ordinary one-cell float64 profile")
    return {"display": node_id(display), "handle": node_id(handle), "dimension": node_id(dimension),
            "parameter": node_id(parameter), "dimension_id": dimension["f50"], "presentation_code": display["f58"],
            "stored_value": parameter["f58"], "cached_display": unpack("<d", array["data"])[0]}


def atom(operation, key):
    (row,) = operation[key]["items"]
    value = row["o"]
    require(value.cls == "moAtom_c", "unexpected pattern lineage object")
    return value


def atom_proof(root, pattern, seed, features):
    plate, seed_body, final = (atom(node, "f528") for node in (features[32], seed, pattern))
    (row,) = pattern["f548"]["items"]
    wrapper = row["o"]
    actual_atoms = tuple(entry["o"] for entry in root["fd88"]["atoms"])
    lineage_rows = (plate, seed_body, final)
    ids = tuple(item["f140"] for item in lineage_rows)
    require(tuple(item["f144"] for item in lineage_rows) == (1, 1, 0)
            and all(item in actual_atoms for item in lineage_rows)
            and atom(seed, "f530") is plate and atom(pattern, "f530") is seed_body
            and pattern["f498"] == [{"v": ids[2]}] and len(set(ids)) == 3
            and tuple(item["f130"] for item in lineage_rows) == (32, seed["f08"], pattern["f08"]),
            "pattern does not consume the actual seed's joined stock")
    require(pattern["f544"] == pattern["has_f548"] == 1 and wrapper.cls == "moCompSolidBody_c"
            and wrapper["f18"] == wrapper["f1c"] == ids[1]
            and [row["v"] for row in wrapper["f110"]] == [ids[1], ids[0]]
            and wrapper["f58"]["owner"] is root and wrapper["f108"] == plate["f130"]
            and wrapper["ff0"].cls == "moFaceRef_c", "pattern scoped wrapper lost the actual lineage")
    return {"atom_ids": ids, "producer_ids": [item["f130"] for item in lineage_rows],
            "retired_consumed": True, "wrapper": node_id(wrapper),
            "wrapper_base_producer": wrapper["f108"], "wrapper_lineage": [row["v"] for row in wrapper["f110"]],
            "wrapper_remap": [wrapper["f100"], wrapper["f104"]], "wrapper_face_class": wrapper["ff0"].cls}


def pattern_proof(archive, cfg_doc, resolved, reopened):
    features = {node["f08"]: node for node in resolved.roots}
    (pattern,) = tuple(node for node in resolved.roots if node.cls == "moLPattern_c")
    (row,) = pattern["f988"]["items"]
    seed = row["o"]
    source = reopened["pattern"]
    require(features[seed["f08"]] is seed and seed.cls == "moICE_c" and pattern["f820"] is None
            and pattern["f9d8"].get("n") == 0 and source["skipped_items"] == []
            and [node_name(seed)] == [item["name"] for item in source["seeds"]],
            "actual seed or skip array disagrees with native selection")
    line = pattern["f1288"]
    plane_ref = line["f58"]
    ref_id = plane_ref["ff0"]["f00"]
    plane = features[ref_id]
    epoch = plane_ref["ff0"]["f08"]
    headers = tuple(ReadHeaderGraph(archive.require(name), VERSION) for name in ("Header2", CFG + "-ModelHeader"))
    require(line.cls == "moLineRef_w" and plane_ref.cls == "moCompRefPlane_c"
            and plane_ref["f58"]["owner"] is cfg_doc.roots[0] and plane.cls == "moRefPlane_c"
            and all(DatumTime(header, ref_id) == epoch for header in headers)
            and pattern["f1278"] is pattern["f1280"] is pattern["f1290"] is None,
            "direction does not bind an actual local datum in both headers")
    direction = reopened["direction"]
    axis = vector(line["fe0"])
    flipped = pattern["f1298"]
    signed = tuple((-1 if flipped else 1) * value for value in axis)
    ref_bytes = bytes.fromhex(source["plane_feature_reference"]["hex"])
    require(len(ref_bytes) == source["plane_feature_reference"]["bytes"]
            and int.from_bytes(ref_bytes[-4:], "little") == ref_id
            and axis == tuple(direction["reference_plane_normal_model"])
            and signed == tuple(direction["signed_direction_sketch"]) and flipped == int(direction["reverse"]),
            "actual selected datum or signed direction differs from the native direction receipt")
    dims = {slot: display_value(pattern, slot) for slot in ("f1258", "f1260", "f1268", "f1270", "f1318", "f1320")}
    count, step, idle = (dims[slot] for slot in ("f1258", "f1260", "f1268"))
    values = source["values"]
    require(count["parameter"]["name"] == "D1" and count["parameter"]["class"] == "moIntegerParameter_c"
            and count["stored_value"] == count["cached_display"] == values["D1TotalInstances"]
            and step["parameter"]["name"] == "D3" and step["parameter"]["class"] == "moLengthParameter_c"
            and step["stored_value"] == step["cached_display"] == values["D1Spacing"]
            and idle["parameter"]["name"] == "D2" and idle["stored_value"] == values["D2TotalInstances"] == 1
            and idle["cached_display"] == 0.0 and idle["presentation_code"] == 0
            and all(dims[key]["stored_value"] == dims[key]["cached_display"] == 0
                    for key in ("f1270", "f1318", "f1320")), "actual active and inactive drivers differ")
    return {"feature": node_id(pattern), "feature_id": pattern["f08"], "seed": node_id(seed), "seed_id": seed["f08"],
            "plane": node_id(plane), "plane_id": ref_id, "plane_key": plane_ref["f100"], "plane_epoch": epoch,
            "axis": axis, "reverse": bool(flipped), "signed_axis": signed, "line_point_m": vector(line["fc8"]),
            "dimensions": dims, "scope": atom_proof(cfg_doc.roots[0], pattern, seed, features)}


def analyze(raw, reopened, reg, plans):
    archive = SldprtArchive.from_bytes(raw)
    require(archive.format_version == 4 and ContainerMo(archive.streams) == VERSION, "unexpected source container version")
    prefix = sdk_prefix(archive)
    names = expand(archive, (*REQUIRED, *(name for name in plans if name in archive.streams and name not in REQUIRED)))
    replay, raw_counts = {}, {}
    for name in names:
        if name == "Contents/Definition":
            value = archive.require(name)
            replay[name] = sdk_stream(value, lambda: sdk_definition(value))
            continue
        check = stream_roundtrip(archive, name, reg, plans, linked=True, require_proven=True)
        replay[name] = compact_stream(check)
        if name == RESOLVED:
            raw_counts = {mode: Counter(
                (entry["object_class"], entry["schema"], entry["field"], entry["observed_length"])
                for entry in check["schema_usage"][mode]["raw_operations"]
            ) for mode in ("load", "store")}
    require(all(value["exact_without_tail"] for value in replay.values()) and len(replay) == 15,
            "a disclosed archive had unexpected replay behavior")
    expected_raw = {("moDisplayDim_c", "dm.FUN_4bd03960", "data", 8): 2,
                    ("moDisplayDistanceDim_c", "dm.FUN_4bd03960", "data", 8): 6}
    require(raw_counts["load"] == raw_counts["store"] == expected_raw and
            all(value["exact_without_raw"] for name, value in replay.items() if name != RESOLVED),
            "archive has a new raw dependency")
    cfg_doc, cfg = load_config(archive.require(CFG), reg, VERSION, archive=archive, name=CFG)
    resolved, resolution = load_resolved(archive.require(RESOLVED), reg, VERSION, archive=archive,
                                        name=RESOLVED, seed=cfg.map_state())
    proof = pattern_proof(archive, cfg_doc, resolved, reopened)
    (pattern,) = (node for node in resolved.roots if node.cls == "moLPattern_c")
    require(not resolved.tail and pattern.pos == prefix["class_tag_offset"] and pattern.index == proof["feature"]["archive_object"],
            "research replay reached a different pattern root")
    doc = open_document(raw, source_format="solidworks.sldprt", strict=True)
    (feature,) = (value for value in doc.feature_timeline if value.name == node_name(pattern))
    fallback = feature.definition.object_data
    require(type(feature.definition).__name__ == "NativeFeatureDefinition"
            and len(doc.bodies) == len(doc.brep.bodies) == reopened["bodies"] == 1,
            "public generic fallback and stored body count differ")
    return {"native_sha256": digest(raw), "streams": replay, "container_stream_count": len(archive.streams),
            "sdk_prefix": prefix, "research_pattern_span": [pattern.pos, pattern.end],
            "resolved_counter": resolution.count, "typed_pattern_evidence": proof,
            "resolved_raw_fields_per_direction": [
                {"object_class": cls, "schema": schema, "field": field, "bytes": width, "operations": count}
                for (cls, schema, field, width), count in sorted(expected_raw.items())
            ], "public_cached_bodies": len(doc.bodies), "public_generic_selection_kind": fallback["operation"]["selection_kind"],
            "native_mass_properties": reopened["mass"]}


def measure(packet):
    require(packet.name == "LinearPatternSourcePacket03", "use only the disclosed packet")
    lock = json.loads(checked(packet / "Progress" / "disclosed-lock.json", PIN))
    area = packet / "DisclosedNative"
    require(lock["cohort"] == "disclosed" and lock["passed"] and lock["writer_output_count"] == 0
            and lock["completed_native_phases"] == lock["distinct_processes"] == lock["expected_native_phases"] == 14
            and lock["inputs_unchanged"] and lock["packet_unchanged"] and lock["control_unchanged"]
            and lock["application_pids_before"] == lock["application_pids_after"] == [], "source custody differs")
    controls = []
    for side in ("before", "after"):
        report = lock["controls"][side]
        saved = json.loads(checked(area / f"Control{side.title()}.json", report["record_sha256"]))
        identity = saved["oracle_identity"]
        require(report["passed"] and saved["open_errors"] == saved["open_warnings"] == 0 and saved["rebuilt"]
                and saved["sha256"] == lock["control_sha256"] and not saved["dialogs"]
                and identity["file_version"] == "34.5.2.0604" and identity["sha256"] == lock["oracle_sha256"],
                "native bracket failed")
        controls.append(identity["process_creation_filetime"])
    rows, processes = [], []
    reg = registry()
    plans = PLANS | reg.plans
    require(tuple(value["name"] for value in lock["cases"]) == LABELS, "unexpected disclosed case set")
    for case in lock["cases"]:
        label = case["name"]
        require(case["passed"] and case["split"] == "disclosed" and
                tuple(row["phase"] for row in case["phases"]) == ALL_PHASES, "expected full disclosed source lifecycle")
        seen = {}
        for row in case["phases"]:
            phase = row["phase"]
            value = json.loads(checked(area / label / phase / "Record.json", row["record_sha256"]))
            identity = value["oracle_identity"]
            require(value["passed"] and row["passed"] and identity["sha256"] == lock["oracle_sha256"]
                    and identity["file_version"] == "34.5.2.0604" and not value["dialogs"], "disclosed phase differs")
            processes.append(identity["process_creation_filetime"])
            seen[phase] = value
        for suffix, phase, result in zip(("", "Spacing", "Instances"), SOURCE_PHASES, case["native_sources"], strict=True):
            name = label + suffix + ".SLDPRT"
            observation = seen[phase]
            require(name == result["name"] and result["sha256"] == observation["native_sha256"]
                    and observation["open"] == {"opened": True, "errors": 0, "warnings": 0}, "immutable reread differs")
            raw = checked(area / label / name, result["sha256"], result["bytes"])
            rows.append({"name": name, "phase": phase, **analyze(raw, observation["reopened"], reg, plans)})
    require(len(set((*processes, *controls))) == 14 and all(controls[0] < value < controls[1] for value in processes),
            "oracle controls did not bracket all disclosed phases")
    return rows


def main(output, packet):
    check_output(("git", "merge-base", "--is-ancestor", REVISION, "HEAD"), cwd=ROOT)
    scope = ("src", "re/tooling/sw2026/serial", "re/tooling/sw2026/AuditArchiveCorpus.py",
             "re/tooling/sw2026/AuditKeywordCorpus.py")
    require(not check_output(("git", "diff", "--name-only", REVISION, "--", *scope), cwd=ROOT),
            "audit requires the exact pinned codec tree")
    results = measure(packet)
    require(not any(name in ("Swapp", "pythoncom", "pywintypes") or name.startswith("win32com")
                    for name in sys.modules), "host data audit loaded an oracle dependency")
    summary = {"schema": "kit.sw2026.local-linear-pattern-disclosed-archive-intake.v1",
               "codec_revision": REVISION, "codec_source_tree": check_output(
                   ("git", "rev-parse", REVISION + ":src"), cwd=ROOT, text=True,
               ).strip(), "native_source_lock_sha256": PIN, "audit_tool_sha256": digest(HERE.read_bytes()),
               "native_oracle_phases_rechecked": 14, "native_processes_started": 0, "heldout_inputs_read": 0,
               "native_files_written": 0, "cases": results}
    raw = (json.dumps(summary, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with output.open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"snapshots": len(results), "exact_replays": sum(len(row["streams"]) for row in results),
                      "receipt_sha256": digest(raw)}))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    main(args.output, args.packet)
