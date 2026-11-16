from __future__ import annotations

import argparse
import hashlib
import json
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
CORPUS = ROOT / "re/solidworks/v2026/corpus/end-conditions"
LOCK = ROOT / "re/solidworks/v2026/heldout/EndConditionSourceLock.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def read_object(path):
    value = json.loads(path.read_bytes())
    require(isinstance(value, dict), "expected a JSON object")
    return value


def exactly(values, label):
    require(len(values) == 1, f"expected exactly one {label}, found {len(values)}")
    return values[0]


def object_type(value, name):
    require(isinstance(value, Obj) and value.cls == name, f"expected actual {name} node")
    return value


def display_parameter(value):
    if value is None:
        return None
    require(isinstance(value, Obj) and value.cls in ("moDisplayDistanceDim_c", "moDisplayAngularDim_c"), "end specification has another display class")
    handle = object_type(exactly(value["f850"], "display model handle")["o"], "moFeatureDimHandle_c")
    dimension = handle["ff0"]
    require(isinstance(dimension, Obj) and dimension.cls in ("ParallelPlaneDistanceDim_c", "AngleDim_c"), "end specification has another dimension class")
    parameter = object_type(dimension["f28"], "moAngleParameter_c" if dimension.cls == "AngleDim_c" else "moLengthParameter_c")
    require(isinstance(parameter, Obj) and parameter.cls in ("moLengthParameter_c", "moAngleParameter_c"), "end specification has another parameter class")
    return {"display_class": value.cls, "dimension_class": dimension.cls, "parameter_class": parameter.cls, "name": parameter["f18"]["f08"], "value": parameter["f58"]}


def observations(models):
    reader = models[RESOLVED]["reader"]
    objects = {id(entry[1]): entry[1] for entry in reader.table.values() if entry[0] == "obj" and isinstance(entry[1], Obj)}
    feature = exactly([item for item in objects.values() if item.cls == "moExtrusion_c"], "extrusion feature")
    profile = exactly([item for item in objects.values() if item.cls == "moProfileFeature_c"], "ordinary profile")
    require(feature["f18"]["f08"] == "CurveBoss" and profile["f18"]["f08"] == "CurveSketch", "authored feature names changed")
    require(any(item["o"] is profile for item in feature["f60"]["list"]["items"]), "extrusion lost its actual profile dependency")
    end = object_type(feature["f818"], "moEndSpec_c")
    scalars = {name: end[name] for name in ("f08", "f88", "f8c", "f0c", "f10", "fa0", "fb8", "fbc", "fc0", "fc4", "fb0", "fb4", "fa8", "fac", "fd8", "fdc", "f128", "f12c", "f130", "f148", "f14c", "f150", "f154", "f158")}
    require(all(value is None or type(value) in (int, float) for value in scalars.values()), "end-spec scalar owner has another type")
    dimensions = {name: display_parameter(end[name]) for name in ("f18", "f20", "fc8", "fd0")}
    graph = GraphProof(models[RESOLVED]["document"], reader, RESOLVED, models["Contents/Config-0"])
    require(graph["unresolved_references"] == 0, "source linked graph has unresolved references")
    return {"scalars": scalars, "dimensions": dimensions, "from_type": object_type(end["f140"], "moFromEndSpec_c")["t"], "explicit_direction_is_null": end["f138"] is None, "forward_surface_array_present": bool(end["has_f28"]), "reverse_surface_array_present": bool(end["has_f48"]), "graph": graph}


def fixture_inputs():
    manifest = read_object(CORPUS / "Manifest.json")
    proof = read_object(CORPUS / "SourceEvidence.json")
    lock = read_object(LOCK)
    specification_path = HERE.parent / "EndConditionSpecs.json"
    specification = read_object(specification_path)
    expected = {case["name"]: case for case in specification["cases"] + specification["controls"] if case["split"] in ("discovery", "control")}
    require(len(expected) == 14, "source membership must be twelve discovery inputs and two controls")
    require(manifest["schema"] == "kit.sw2026.end-source-fixtures.v1" and proof["schema"] == "kit.sw2026.end-source-preparation.v1", "unexpected source fixture schema")
    require(manifest["is_writer_output"] is manifest["native_acceptance_inherited"] is manifest["heldout_native_payloads_read"] is False, "source fixture scope differs")
    require(proof["archive_schemas_executed"] is proof["container_outputs_reparsed"] is proof["heldout_native_payloads_read"] is False, "preparation exceeded its container-only scope")
    require(proof["manifest_sha256"] == digest((CORPUS / "Manifest.json").read_bytes()), "fixture manifest fingerprint differs")
    require(proof["privacy_ledger_sha256"] == manifest["privacy_ledger_sha256"] == digest((CORPUS / "PrivacyLedger.json").read_bytes()), "privacy ledger fingerprint differs")
    require(proof["source_lock_sha256"] == manifest["source_lock_sha256"] == digest(LOCK.read_bytes()), "source lock fingerprint differs")
    require(lock["specs_sha256"] == digest(specification_path.read_bytes()), "source lock differs from neutral specifications")
    require(proof["preparer_sha256"] == digest((HERE.parent / "PrepareEndConditions.py").read_bytes()) and proof["privacy_helper_sha256"] == digest((HERE.parent / "PrepareCurveCorpus.py").read_bytes()), "source preparation implementation differs")
    require(proof["owner_verification_sha256"] == manifest["owner_verification_sha256"] and proof["owner_verification"]["all_checks_passed"] is True, "owner verification identity differs")
    locked = {case["name"]: case for case in lock["cases"] if case["name"] in expected}
    entries = manifest["records"]
    require(len(entries) == len(locked) == 14 and {entry["name"] for entry in entries} == set(expected), "prepared source membership differs")
    require({path.name for path in CORPUS.glob("*.SLDPRT")} == {name + ".SLDPRT" for name in expected}, "unexpected native source file")
    for entry in entries:
        require(entry["spec"] == expected[entry["name"]] and entry["split"] in ("discovery", "control"), "prepared source differs from its independent neutral specification")
        require(entry["file"] == entry["name"] + ".SLDPRT" and entry["source_sha256"] == locked[entry["name"]]["sha256"], "prepared native source identity differs")
    return manifest, entries


def inspect_file(entry):
    path = CORPUS / entry["file"]
    require(not path.is_symlink() and path.resolve().parent == CORPUS.resolve(), "source path escaped its corpus")
    raw = path.read_bytes()
    require(digest(raw) == entry["sha256"] and len(raw) == entry["bytes"], "prepared native fingerprint differs")
    archive = SldprtArchive.from_bytes(raw, path)
    streams = {row["name"]: row for row in entry["streams"]}
    require(len(streams) == len(entry["streams"]) and set(archive.streams) == set(streams), "prepared stream membership differs")
    require(all(digest(data) == streams[name]["sha256"] and len(data) == streams[name]["bytes"] for name, data in archive.streams.items()), "prepared stream identity differs")
    reg = registry()
    plans = {**PLANS, **reg.plans}
    primary = one(path, list(PRIMARY), reg, plans, False, True)
    linked = one(path, [RESOLVED], reg, plans, True, True)
    result = {"file": entry["file"], "source_sha256": entry["source_sha256"], "sha256": entry["sha256"], "specification": entry["spec"], "native_definition": entry["source_observations"]["author"]["extrusion"], "primary": primary, "linked": linked, "passed": False}
    require(primary["passed"] is linked["passed"] is True, "complete critical archive comparison failed")
    result["observed_end_spec"] = observations(LoadModels(archive, reg))
    require(path.read_bytes() == raw, "source fixture changed during inspection")
    result["source_immutable"] = result["passed"] = True
    return result


def main():
    parser = argparse.ArgumentParser(description="Inspect complete locked end-condition discovery archives in a fresh process")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = {"schema": "kit.sw2026.end-source-reader.v1", "passed": False, "pid": os.getpid(), "is_writer_output": False, "native_acceptance_inherited": False, "heldout_native_payloads_read": False, "files": []}
    try:
        manifest, entries = fixture_inputs()
        report.update(manifest_sha256=digest((CORPUS / "Manifest.json").read_bytes()), source_lock_sha256=manifest["source_lock_sha256"], source_proof=[{"file": str(Path(__file__).relative_to(ROOT)), "sha256": digest(Path(__file__).read_bytes())}, *SourceProof()])
        for entry in entries:
            try:
                result = inspect_file(entry)
            except Exception as error:
                result = {"file": entry["file"], "passed": False, "error": repr(error), "trace": traceback.format_exc(limit=10)}
            report["files"].append(result)
        report["file_count"] = len(report["files"])
        report["stream_count"] = sum(len(row.get(role, {}).get("streams", {})) for row in report["files"] for role in ("primary", "linked"))
        report["passed"] = len(report["files"]) == 14 and all(row["passed"] for row in report["files"])
    except Exception as error:
        report.update(error=repr(error), trace=traceback.format_exc(limit=10))
    with args.report.open("x", encoding="utf-8") as output:
        output.write(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + "\n")
    print(json.dumps({key: report[key] for key in ("passed", "file_count", "stream_count") if key in report}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
