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
from SavedCircles import compact, exactly, handle_index, number, object_type, parameter
from StringCorpus import GraphProof, LoadModels, SourceProof
from TreeNames import document_views, read_object, require
from convert.adapters.solidworks.Container.Container import SldprtArchive

CORPUS = ROOT / "re/solidworks/v2026/corpus/tree-parity-saves"
RECEIPT = ROOT / "re/solidworks/measurements/2026/TreeParityInspection01.json"
GENERATED = ROOT / "re/solidworks/measurements/2026/TreeHeldoutProcessesE727.json"
RESOLVED = "Contents/Config-0-ResolvedFeatures"
PHASES = ("open-save", "edit-save", "edited-fresh")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def fixture_inputs():
    manifest = read_object(CORPUS / "Manifest.json")
    proof = read_object(CORPUS / "SourceEvidence.json")
    receipt = read_object(RECEIPT)
    generated = read_object(GENERATED)
    require(manifest["schema"] == "kit.sw2026.tree-parity-fixtures.v1" and proof["schema"] == "kit.sw2026.tree-parity-preparation.v1", "unexpected tree-parity fixture schemas")
    require(manifest["is_writer_output"] is manifest["native_acceptance_inherited"] is manifest["heldout_native_payloads_read"] is False, "tree-parity fixture scope differs")
    require(proof["manifest_sha256"] == digest((CORPUS / "Manifest.json").read_bytes()), "tree-parity manifest hash differs")
    require(proof["privacy_ledger_sha256"] == manifest["privacy_ledger_sha256"] == digest((CORPUS / "PrivacyLedger.json").read_bytes()), "tree-parity privacy ledger differs")
    require(proof["source_receipt_sha256"] == manifest["source_receipt_sha256"] == digest(RECEIPT.read_bytes()), "tree-parity native receipt differs")
    require(proof["prediction_receipt_sha256"] == manifest["prediction_receipt_sha256"] == receipt["prediction_receipt_sha256"] == digest(GENERATED.read_bytes()), "tree-parity prediction receipt differs")
    require(proof["source_job_sha256"] == manifest["source_job_sha256"] == receipt["job_sha256"], "tree-parity native job differs")
    for key, filename in (("preparer_sha256", "PrepareTreeParity.py"), ("privacy_helper_sha256", "PrepareCurveCorpus.py"), ("saved_helper_sha256", "PrepareSavedCircles.py")):
        require(proof[key] == digest((HERE.parent / filename).read_bytes()), "tree-parity preparation source differs")
    require(proof["archive_schemas_executed"] is proof["container_outputs_reparsed"] is proof["heldout_native_payloads_read"] is False, "tree-parity preparation exceeded its scope")
    require(receipt["passed"] and receipt["bounded_tree_pose_rung_passed"] and receipt["controls_healthy"] and receipt["inputs_immutable"], "tree-parity native measurements did not pass")
    require(receipt["native_acceptance"] is receipt["heldout_acceptance"] is False, "tree-parity native acceptance scope differs")
    require(manifest["generator_revision"] == receipt["generator"]["writer_revision"] == generated["writer_revision"], "tree-parity writer revisions differ")
    observations = {(case["name"], phase["phase"]): phase for case in receipt["cases"] for phase in case["candidate"]}
    predictions = {item["name"]: item for item in generated["outputs"]}
    expected_files = {f"{name}-{phase}.SLDPRT" for name in predictions for phase in PHASES}
    records = manifest["records"]
    require(len(predictions) == 2 and len(observations) == len(records) == len(expected_files) == 6, "tree-parity fixture membership differs")
    require({x["file"] for x in records} == {x.name for x in CORPUS.glob("*.SLDPRT")} == expected_files, "tree-parity native file membership differs")
    observed_records = []
    for entry in records:
        phase = observations[entry["name"], entry["phase"]]
        require(phase["lane"] == "candidate" and phase["passed"] and phase["source_immutable"], "tree-parity candidate phase differs")
        require(entry["source_sha256"] == phase["saved_sha256"] and entry["source_bytes"] == phase["saved_bytes"], "tree-parity native saved identity differs")
        require(entry["is_writer_output"] is entry["native_acceptance_inherited"] is False, "tree-parity derivative was misclassified")
        document = predictions[entry["name"]]["request"]["document"]
        factors = phase["saved_factors"]
        require(factors == ([1.0, 1.0, 1.0] if entry["phase"] == PHASES[0] else [1.07, 0.89, 1.0]), "tree-parity native edit factors differ")
        expected = {key: document[key] for key in ("center_m", "radius_m", "depth_m", "plane_axis", "sketch_name", "extrusion_name", "end_condition", "reverse_direction")}
        expected.update(radius_m=document["radius_m"] * factors[0], depth_m=document["depth_m"] * factors[1], mode=document["circle_dimension"]["mode"])
        expected.update(native_frame=phase["snapshot"]["frame"], native_saved_pose=phase["scenes"]["saved"]["pose"])
        require(entry["expected"] == expected, "tree-parity semantic targets differ from the neutral prediction and independent native measurements")
        observed_records.append({**entry, "native_model_to_sketch": phase["snapshot"]["model_to_sketch_transform"]})
    return manifest, observed_records


def sketch_state(objects, expected, native_transform):
    profile = exactly([x for x in objects if x.cls == "moProfileFeature_c"], "ordinary sketch feature")
    boss = exactly([x for x in objects if x.cls == "moExtrusion_c"], "native extrusion feature")
    require(profile["f18"]["f08"] == expected["sketch_name"] and boss["f18"]["f08"] == expected["extrusion_name"], "tree-parity feature names differ")
    require(any(x["o"] is profile for x in boss["f60"]["list"]["items"]), "tree-parity boss lost its actual sketch dependency")
    sketch = object_type(profile["pd_f80"], "sgSketch")
    require(len(sketch["arcs"]) == 1 and not sketch["lines"], "tree-parity sketch is not one ordinary circle")
    arc = sketch["arcs"][0]["arc"]
    start, end, center_index = (compact(arc, name) for name in ("fc8", "fcc", "fdc"))
    points = sketch["points"]
    require(len(points) == 2 and start == end and start != center_index, "tree-parity circle topology differs")
    require(all(type(index) is int and 0 <= index < len(points) for index in (start, center_index)), "tree-parity circle point reference is invalid")
    center, marker = points[center_index]["point"]["pos"], points[start]["point"]["pos"]
    checks = []
    number(checks, "center_x", center["x"], expected["center_m"][0])
    number(checks, "center_y", center["y"], expected["center_m"][1])
    number(checks, "geometry_radius", math.hypot(marker["x"] - center["x"], marker["y"] - center["y"]), expected["radius_m"])
    dimension = object_type(exactly(sketch["dims"]["val_g1"], "radial value")["d"], "sgCircleDim")
    require(dimension["f80"] == (15 if expected["mode"] == "diameter" else 3) and dimension["f68"] == 0, "tree-parity radial mode or driving state differs")
    require(handle_index(object_type(dimension["h1"], "sgArcHandle")) == 0, "tree-parity radial value lost its circle target")
    value = object_type(dimension["f28"], "moLengthParameter_c")
    require(value["f18"]["f08"] == "D1", "tree-parity radial parameter was renamed")
    number(checks, "radial_parameter", value["f58"], expected["radius_m"] * (2 if expected["mode"] == "diameter" else 1))
    relation = exactly([x["d"] for x in sketch["dims"]["log_g1"] if x["d"]["f80"] == 0x11], "fixed center relation")
    require(handle_index(object_type(relation["h1"], "sgPointHandle")) == center_index, "tree-parity fixed relation lost its center target")
    display = object_type(exactly(sketch["dims"]["f118"]["items"], "radial display")["o"], "moDisplayRadialDim_c")
    handle = object_type(exactly(display["f850"], "radial display handle")["o"], "moSkDimHandleRadial_c")
    require(handle["ff0"] is sketch and handle["ff8"] == 0, "tree-parity radial display lost its actual sketch/value owner")
    end_spec = object_type(boss["f818"], "moEndSpec_c")
    require(expected["end_condition"] == "blind" and end_spec["f08"] == 1 and end_spec["f0c"] == end_spec["f10"] == end_spec["f88"] == 0, "tree-parity boss is no longer single-ended blind")
    require(end_spec["f8c"] == int(expected["reverse_direction"]), "tree-parity boss reversed direction differs")
    depth = parameter(object_type(end_spec["f18"], "moDisplayDistanceDim_c"))["f58"]
    number(checks, "depth_parameter", depth, expected["depth_m"])
    frame = profile["pd_ff0"]
    require(len(native_transform) == 16 and native_transform[12:] == [1.0, 0.0, 0.0, 0.0], "native model-to-sketch transform is not the claimed rigid frame")
    native_frame = expected["native_frame"]
    u, v = native_frame["u"], native_frame["v"]
    normal = [u[(i + 1) % 3] * v[(i + 2) % 3] - u[(i + 2) % 3] * v[(i + 1) % 3] for i in range(3)]
    basis = (u, v, normal)
    inverse_matrix = [basis[col][row] for row in range(3) for col in range(3)]
    inverse_translation = [-sum(axis[component] * native_frame["origin"][component] for component in range(3)) for axis in basis]
    require(native_transform[:12] == [*inverse_matrix, *inverse_translation], "native model-to-sketch transform does not invert the observed sketch placement")
    for name, target in zip(("f58", "f60", "f68"), native_transform[9:12], strict=True):
        number(checks, "frame_" + name, frame[name], target)
    number(checks, "frame_scale", frame["f70"], native_transform[12])
    matrix = frame["f08"] if frame["has_matrix"] else {f"m{index}": float(index in (0, 4, 8)) for index in range(9)}
    for index, target in enumerate(native_transform[:9]):
        number(checks, "frame_m" + str(index), matrix[f"m{index}"], target)
    return {"passed": True, "checks": checks, "radial_mode": expected["mode"], "center_fixed": True, "display_linked_to_actual_sketch": True, "reverse_direction": expected["reverse_direction"], "plane_axis": expected["plane_axis"]}


def pose_state(document, expected):
    state = document_views(document)
    orientation = state["default_transform_fae8"]
    pan = state["second_transform_faf0"]
    native = expected["native_saved_pose"]
    require(len(native["orientation"]) == 16 and len(native["translation"]) == 3, "tree-parity native pose shape differs")
    require(orientation["f78"] == pan["f78"] == 0 and not pan["has_matrix"], "tree-parity orthographic transform flags differ")
    matrix = orientation["f08"] if orientation["has_matrix"] else {f"m{index}": float(index in (0, 4, 8)) for index in range(9)}
    checks = []
    for index, target in enumerate(native["orientation"][:9]):
        number(checks, "orientation_" + str(index), matrix[f"m{index}"], target)
    for name in ("f58", "f60", "f68"):
        number(checks, "orientation_neutral_" + name, orientation[name], 0.0)
    number(checks, "orientation_neutral_scale", orientation["f70"], 1.0)
    for name, target in zip(("f58", "f60", "f68"), native["translation"], strict=True):
        number(checks, "pan_" + name, pan[name], target)
    number(checks, "pan_scale", pan["f70"], native["scale2"])
    return {"passed": True, "checks": checks, "document_view_state": state}


def inspect_file(entry):
    path = CORPUS / entry["file"]
    require(not path.is_symlink() and path.resolve().parent == CORPUS.resolve(), "tree-parity fixture escaped its corpus")
    raw = path.read_bytes()
    require(digest(raw) == entry["sha256"] and len(raw) == entry["bytes"], "tree-parity prepared fingerprint differs")
    archive = SldprtArchive.from_bytes(raw, path)
    streams = {row["name"]: row for row in entry["streams"]}
    require(len(streams) == len(entry["streams"]) and set(archive.streams) == set(streams), "tree-parity prepared stream membership differs")
    require(all(digest(data) == streams[name]["sha256"] and len(data) == streams[name]["bytes"] for name, data in archive.streams.items()), "tree-parity prepared stream fingerprint differs")
    reg = registry()
    plans = {**PLANS, **reg.plans}
    primary = one(path, [*REQUIRED, "Header2"], reg, plans, False, True)
    linked = one(path, [RESOLVED], reg, plans, True, True)
    result = {"file": entry["file"], "name": entry["name"], "phase": entry["phase"], "sha256": entry["sha256"], "source_sha256": entry["source_sha256"], "primary": primary, "linked": linked, "passed": False}
    require(primary["passed"] is linked["passed"] is True, "tree-parity complete critical archive comparison failed")
    models = LoadModels(archive, reg)
    reader = models[RESOLVED]["reader"]
    objects = {id(item[1]): item[1] for item in reader.table.values() if item[0] == "obj" and isinstance(item[1], Obj)}
    markup = exactly([x for x in objects.values() if x.cls == "moInkMarkupFolder_c"], "actual markup folder")
    require(markup["f18"]["f08"] == "Markups" and markup["f360"] == 1 and markup["f370"] == 0, "tree-parity actual markup folder state differs")
    result["markup_folder"] = {"class": markup.cls, "node_name": markup["f18"]["f08"], "f360": markup["f360"], "f370": markup["f370"]}
    result["semantics"] = sketch_state(list(objects.values()), entry["expected"], entry["native_model_to_sketch"])
    result["pose"] = pose_state(models["Contents/Definition"]["document"].head, entry["expected"])
    result["linked_graph"] = GraphProof(models[RESOLVED]["document"], reader, RESOLVED, models["Contents/Config-0"])
    require(result["linked_graph"]["unresolved_references"] == 0, "tree-parity linked graph has unresolved references")
    require(path.read_bytes() == raw, "tree-parity fixture changed during decoding")
    result["source_immutable"] = result["passed"] = True
    return result


def main():
    parser = argparse.ArgumentParser(description="Read six candidate-saved derivatives through complete archives, linked graph, circle semantics, actual markup class and independent native pose")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = {"schema": "kit.sw2026.tree-parity-reader.v1", "passed": False, "is_writer_output": False, "native_acceptance_inherited": False, "heldout_native_payloads_read": False, "pid": os.getpid(), "files": [], "scope": "Complete saved-derivative archive/graph/semantic and pose readback; no new generated output or original held-out payload decoding"}
    try:
        manifest, entries = fixture_inputs()
        report.update(manifest_sha256=digest((CORPUS / "Manifest.json").read_bytes()), source_receipt_sha256=manifest["source_receipt_sha256"], prediction_receipt_sha256=manifest["prediction_receipt_sha256"])
        report["source_proof"] = [{"file": str(path.relative_to(ROOT)), "sha256": digest(path.read_bytes())} for path in (Path(__file__), HERE / "SavedCircles.py", HERE / "TreeNames.py")] + SourceProof()
        for entry in entries:
            try:
                value = inspect_file(entry)
            except Exception as error:
                value = {"file": entry["file"], "passed": False, "error": repr(error), "trace": traceback.format_exc(limit=10)}
            report["files"].append(value)
        report["file_count"] = len(report["files"])
        report["stream_count"] = sum(len(x.get(kind, {}).get("streams", {})) for x in report["files"] for kind in ("primary", "linked"))
        report["semantic_check_count"] = sum(len(x.get("semantics", {}).get("checks", [])) for x in report["files"])
        report["pose_check_count"] = sum(len(x.get("pose", {}).get("checks", [])) for x in report["files"])
        report["passed"] = len(report["files"]) == 6 and all(x["passed"] for x in report["files"])
    except Exception as error:
        report.update(error=repr(error), trace=traceback.format_exc(limit=10))
    with args.report.open("x", encoding="utf-8") as output:
        output.write(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + "\n")
    print(json.dumps({key: report[key] for key in ("passed", "file_count", "stream_count", "semantic_check_count", "pose_check_count") if key in report}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
