from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))

from Classes import registry
from Core import Obj
from RoundTrip import PLANS, REQUIRED, one
from StringCorpus import GraphProof, LoadModels, SourceProof
from convert.adapters.solidworks.Container.Container import SldprtArchive

PRIMARY = (*REQUIRED, "Header2")
RESOLVED = "Contents/Config-0-ResolvedFeatures"
CORPUS = ROOT / "re/solidworks/v2026/corpus/circle-saves"
RECEIPT = ROOT / "re/solidworks/measurements/2026/CircleBossInspection01.json"
GENERATED = ROOT / "re/solidworks/measurements/2026/CircleBossProcesses993e707.json"
PHASES = ("open-save", "fresh-reopen", "edited-fresh-reopen")
NAMES = ("CircleRadiusBoss", "CircleDiameterBoss")


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def read_object(path):
    value = json.loads(path.read_bytes())
    require(isinstance(value, dict), "expected a JSON object")
    return value


def number(checks, label, actual, expected):
    require(type(actual) in (int, float) and type(expected) in (int, float), f"nonnumeric semantic value: {label}")
    passed = math.isfinite(actual) and math.isfinite(expected) and (actual == expected or format(actual, ".6g") == format(expected, ".6g"))
    checks.append({"label": label, "actual": actual, "expected": expected, "matches_6_significant_figures": passed})
    require(passed, f"saved semantic value differs: {label}: {actual!r} != {expected!r}")


def object_type(value, name):
    require(isinstance(value, Obj) and value.cls == name, f"expected actual {name} node")
    return value


def exactly(values, label):
    require(len(values) == 1, f"expected exactly one {label}, found {len(values)}")
    return values[0]


def compact(fields, name):
    value = fields[name + "_s"]
    return fields[name] if value == 0xFFFF else value


def handle_index(handle):
    return handle["f18"] if handle["idx"] == 0x777F else handle["idx"]


def parameter(display):
    handles = display["f850"]
    handle = object_type(exactly(handles, "feature dimension handle")["o"], "moFeatureDimHandle_c")
    dimension = object_type(handle["ff0"], "ParallelPlaneDistanceDim_c")
    result = object_type(dimension["f28"], "moLengthParameter_c")
    require(result["f18"]["f08"] == "D1", "blind driving parameter was renamed")
    return result


def semantics(models, expected):
    reader = models[RESOLVED]["reader"]
    objects = {id(entry[1]): entry[1] for entry in reader.table.values() if entry[0] == "obj" and isinstance(entry[1], Obj)}
    profile = exactly([item for item in objects.values() if item.cls == "moProfileFeature_c"], "ordinary sketch feature")
    boss = exactly([item for item in objects.values() if item.cls == "moExtrusion_c"], "native extrusion feature")
    require(profile["f18"]["f08"] == expected["sketch_name"] and boss["f18"]["f08"] == expected["extrusion_name"], "authored feature names changed")
    require(any(item["o"] is profile for item in boss["f60"]["list"]["items"]), "saved boss lost its actual profile dependency")
    sketch = object_type(profile["pd_f80"], "sgSketch")
    require(len(sketch["arcs"]) == 1 and not sketch["lines"], "saved profile is not one ordinary circle")
    arc = sketch["arcs"][0]["arc"]
    start, end, center_index = (compact(arc, name) for name in ("fc8", "fcc", "fdc"))
    points = sketch["points"]
    require(len(points) == 2 and start == end and start != center_index, "saved circle lost endpoint/center topology")
    require(all(type(index) is int and 0 <= index < len(points) for index in (start, center_index)), "circle point reference is invalid")
    center, marker = points[center_index]["point"]["pos"], points[start]["point"]["pos"]
    radius = math.hypot(marker["x"] - center["x"], marker["y"] - center["y"])
    checks = []
    number(checks, "center_x", center["x"], expected["center_m"][0])
    number(checks, "center_y", center["y"], expected["center_m"][1])
    number(checks, "geometry_radius", radius, expected["radius_m"])
    dimension = object_type(exactly(sketch["dims"]["val_g1"], "radial value")["d"], "sgCircleDim")
    require(dimension["f80"] == (15 if expected["mode"] == "diameter" else 3) and dimension["f68"] == 0, "saved radial mode or driving state differs")
    require(handle_index(object_type(dimension["h1"], "sgArcHandle")) == 0, "radial value lost its actual circle target")
    value = object_type(dimension["f28"], "moLengthParameter_c")
    require(value["f18"]["f08"] == "D1", "radial parameter was renamed")
    number(checks, "radial_parameter", value["f58"], expected["radius_m"] * (2 if expected["mode"] == "diameter" else 1))
    fixed = [item["d"] for item in sketch["dims"]["log_g1"] if item["d"]["f80"] == 0x11]
    relation = exactly(fixed, "fixed center logical relation")
    require(handle_index(object_type(relation["h1"], "sgPointHandle")) == center_index, "fixed relation does not target the circle center")
    display = object_type(exactly(sketch["dims"]["f118"]["items"], "radial display")["o"], "moDisplayRadialDim_c")
    radial_handle = object_type(exactly(display["f850"], "radial display handle")["o"], "moSkDimHandleRadial_c")
    require(radial_handle["ff0"] is sketch and radial_handle["ff8"] == 0, "radial display lost its actual value-array owner/index")
    end_spec = object_type(boss["f818"], "moEndSpec_c")
    require(end_spec["f08"] == 1 and end_spec["f0c"] == end_spec["f10"] == 0, "saved boss is no longer single-ended blind")
    depth = parameter(object_type(end_spec["f18"], "moDisplayDistanceDim_c"))["f58"]
    number(checks, "depth_parameter", depth, expected["depth_m"])
    frame = profile["pd_ff0"]
    require(expected["plane_axis"] == "z", "saved reader rung requires a canonical front frame")
    for name in ("f58", "f60", "f68"):
        number(checks, "frame_" + name, frame[name], 0.0)
    number(checks, "frame_scale", frame["f70"], 1.0)
    matrix = frame["f08"] if frame["has_matrix"] else {f"m{index}": float(index in (0, 4, 8)) for index in range(9)}
    for index in range(9):
        number(checks, "frame_m" + str(index), matrix[f"m{index}"], float(index in (0, 4, 8)))
    graph = GraphProof(models[RESOLVED]["document"], reader, RESOLVED, models["Contents/Config-0"])
    require(graph["unresolved_references"] == 0, "saved linked graph has unresolved external references")
    return {"passed": True, "checks": checks, "radial_mode": expected["mode"], "center_fixed": True, "display_linked_to_actual_sketch": True, "circle_radius": radius, "radial_value": value["f58"], "depth": depth, "graph": graph}


def fixture_inputs():
    manifest = read_object(CORPUS / "Manifest.json")
    proof = read_object(CORPUS / "SourceEvidence.json")
    receipt = read_object(RECEIPT)
    generated = read_object(GENERATED)
    require(manifest["schema"] == "kit.sw2026.saved-circle-fixtures.v1", "unexpected fixture manifest")
    require(manifest["is_writer_output"] is manifest["native_acceptance_inherited"] is manifest["heldout_native_payloads_read"] is False, "fixture scope differs")
    require(proof["manifest_sha256"] == digest((CORPUS / "Manifest.json").read_bytes()), "fixture manifest hash differs")
    require(proof["privacy_ledger_sha256"] == manifest["privacy_ledger_sha256"] == digest((CORPUS / "PrivacyLedger.json").read_bytes()), "privacy ledger hash differs")
    require(proof["source_receipt_sha256"] == manifest["source_receipt_sha256"] == digest(RECEIPT.read_bytes()), "native receipt hash differs")
    require(proof["source_job_sha256"] == manifest["source_job_sha256"] == receipt["job"]["sha256"], "original job hash differs")
    require(proof["preparer_sha256"] == digest((HERE.parent / "PrepareSavedCircles.py").read_bytes()) and proof["privacy_helper_sha256"] == digest((HERE.parent / "PrepareCurveCorpus.py").read_bytes()), "fixture preparation implementation differs")
    require(proof["archive_schemas_executed"] is proof["container_outputs_reparsed"] is proof["heldout_native_payloads_read"] is False, "preparation execution scope differs")
    expected_files = {f"{name}-{phase}.SLDPRT" for name in NAMES for phase in PHASES}
    records = manifest["records"]
    require(len(records) == len(expected_files) == 6 and {item["file"] for item in records} == expected_files, "saved fixture membership differs")
    require({path.name for path in CORPUS.glob("*.SLDPRT")} == expected_files, "unexpected saved native file")
    observations = {(case["name"], phase["phase"]): phase for case in receipt["cases"] for phase in case["phases"]}
    requests = {item["request"]["document"]["name"]: item for item in generated["cases"]}
    require(manifest["generator_revision"] == receipt["generator"]["source_revision"] == generated["source_revision"], "neutral generator revision differs")
    for item in records:
        phase = observations[item["name"], item["phase"]]
        require(item["source_sha256"] == phase["saved_sha256"], "original saved hash differs")
        require(item["is_writer_output"] is item["native_acceptance_inherited"] is False, "saved fixture misclassified")
        document = requests[item["name"]]["request"]["document"]
        targets = {
            "center_m": document["center_m"], "radius_m": document["radius_m"] * phase["saved_factor"],
            "depth_m": document["depth_m"] * phase["saved_depth_factor"],
            "mode": document["circle_dimension"]["mode"], "plane_axis": document["plane_axis"],
            "sketch_name": document["sketch_name"], "extrusion_name": document["extrusion_name"],
            "radial_factor": phase["saved_factor"], "depth_factor": phase["saved_depth_factor"],
        }
        require(item["expected"] == targets, "prepared semantic targets differ from independent neutral requests and native edit factors")
    return manifest, proof, records


def inspect_file(entry):
    path = CORPUS / entry["file"]
    require(not path.is_symlink() and path.resolve().parent == CORPUS.resolve(), "saved fixture escaped its corpus")
    raw = path.read_bytes()
    require(digest(raw) == entry["sha256"] and len(raw) == entry["bytes"], "prepared saved hash differs")
    archive = SldprtArchive.from_bytes(raw, path)
    recorded_streams = {item["name"]: item for item in entry["streams"]}
    require(len(recorded_streams) == len(entry["streams"]) and set(archive.streams) == set(recorded_streams), "prepared stream membership differs")
    for name, data in archive.streams.items():
        require(digest(data) == recorded_streams[name]["sha256"] and len(data) == recorded_streams[name]["bytes"], "prepared stream hash differs")
    reg = registry()
    plans = {**PLANS, **reg.plans}
    primary = one(path, list(PRIMARY), reg, plans, False, True)
    linked = one(path, [RESOLVED], reg, plans, True, True)
    result = {"file": entry["file"], "source_sha256": entry["source_sha256"], "sha256": entry["sha256"], "primary": primary, "linked": linked, "passed": False}
    if primary["passed"] is not True or linked["passed"] is not True:
        result["error"] = "saved critical archive comparison failed"
        return result
    try:
        result["semantics"] = semantics(LoadModels(archive, reg), entry["expected"])
    except Exception as error:
        result.update(error=repr(error), trace=traceback.format_exc(limit=10))
        return result
    require(path.read_bytes() == raw, "saved fixture changed during inspection")
    result["source_immutable"] = result["passed"] = True
    return result


def main():
    parser = argparse.ArgumentParser(description="Compare complete saved-circle critical archives and neutral edit semantics in a fresh process")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = {"schema": "kit.sw2026.saved-circle-reader.v1", "passed": False, "is_writer_output": False, "native_acceptance_inherited": False, "heldout_native_payloads_read": False, "pid": os.getpid(), "files": []}
    try:
        manifest, proof, entries = fixture_inputs()
        report["manifest_sha256"] = digest((CORPUS / "Manifest.json").read_bytes())
        report["source_receipt_sha256"] = manifest["source_receipt_sha256"]
        report["source_proof"] = [{"file": str(Path(__file__).relative_to(ROOT)), "sha256": digest(Path(__file__).read_bytes())}, *SourceProof()]
        for entry in entries:
            try:
                result = inspect_file(entry)
            except Exception as error:
                result = {"file": entry["file"], "passed": False, "error": repr(error), "trace": traceback.format_exc(limit=10)}
            report["files"].append(result)
        report["file_count"] = len(report["files"])
        report["stream_count"] = sum(len(item.get(kind, {}).get("streams", {})) for item in report["files"] for kind in ("primary", "linked"))
        report["numeric_count"] = sum(len(item.get("semantics", {}).get("checks", [])) for item in report["files"])
        report["passed"] = bool(report["files"]) and all(item["passed"] for item in report["files"])
    except Exception as error:
        report.update(error=repr(error), trace=traceback.format_exc(limit=10))
    with args.report.open("x", encoding="utf-8") as output:
        output.write(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + "\n")
    print(json.dumps({key: report[key] for key in ("passed", "file_count", "stream_count", "numeric_count") if key in report}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
