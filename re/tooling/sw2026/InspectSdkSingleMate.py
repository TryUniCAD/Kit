from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path, PureWindowsPath
from shutil import copyfileobj

from AuthorCurves import digest, require, write_json
from InspectCombinedPlanarMates import ORACLE, TOOLS as SHARED_TOOLS, phase, signature
from PlanarMateEdit import predict_edit
from PrepareDimensionedAssemblyPredictions import occurrence


SCHEMA = "kit.sw2026.sdk-single-distance-native-trial.v1"
TOOLS = (*SHARED_TOOLS, "PrepareDimensionedAssemblyPredictions.py", Path(__file__).name)
PARENT_CONTROL = "7215af0b188510ba86c226a49726acf468b04408badef15ada6b7cfcbbed917b"
PART_CONTROL = "d91eedc26b1f1289a05b97bc06627e38467ead96d9a1fb4042dc992fec26dc0c"


def checked(path, sha):
    path = path.resolve(strict=True)
    require(path.is_file() and digest(path) == sha, f"the frozen assembly trial file differs: {path.name}")
    return path


def verify(packet, sha):
    root = packet.parent.resolve(strict=True)
    job = json.loads(checked(packet, sha).read_bytes())
    require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE and job["heldout_inputs_read"] == 0,
            "expected the exact disclosed SDK assembly trial")
    tools = (root / "Tools").resolve(strict=True)
    require(Path(__file__).resolve().parent == tools and set(job["tools_sha256"]) == set(TOOLS),
            "assembly observer source set differs")
    for name, expected in job["tools_sha256"].items():
        checked(tools / name, expected)
    fixture = json.loads(checked(root / "Fixture.json", job["fixture_sha256"]).read_bytes())
    prediction = json.loads(checked(root / "Prediction.json", fixture["prediction_sha256"]).read_bytes())
    require(fixture["heldout_inputs_read"] == 0 and fixture["typed_stream_round_trips"] == 22
            and fixture["independent_composer_matches"], "the assembly generation evidence is incomplete")
    checked(root / "NeutralRequest.json", fixture["request_sha256"])
    checked(root / "SourceManifest.json", fixture["source_manifest_sha256"])
    reports = {}
    for name, expected in fixture["phase_receipts"].items():
        reports[name] = json.loads(checked(root / (name + ".stdout"), expected).read_bytes())
        require(reports[name]["passed"] and not reports[name]["runtime_input_file_reads"], "guarded assembly construction was incomplete")
    first, second = (dict(reports[name]) for name in ("BuildA", "BuildB"))
    require(first.pop("worker_pid") != second.pop("worker_pid") and first == second,
            "the guarded assembly candidate must reproduce in separate processes")
    require(set(fixture["files"]) == {"SdkDistanceXAlpha.SLDASM", "SdkDatumPlateAlpha.SLDPRT"}, "unexpected single SDK pair")
    paths = {}
    for name, row in fixture["files"].items():
        path = checked(root / "FrozenGenerated" / name, row["sha256"])
        native = PureWindowsPath(row["encoded_path"])
        key = "assembly" if native.suffix.upper() == ".SLDASM" else "child"
        require(native.is_absolute() and native.name == name and path.stat().st_size == row["bytes"]
                and reports["BuildA"][key]["sha256"] == row["sha256"], "generated pair staging or digest differs")
        paths[key] = (path, native, row["sha256"])
    require(paths["assembly"][1].parent == paths["child"][1].parent, "the native SDK pair must share one directory")
    control = json.loads(checked(root / "ControlCase.json", job["control_case_sha256"]).read_bytes())
    lock = root.parent / prediction["controls"]["relative_directory"]
    source = (checked(lock / "A18PlaneDistance.SLDASM", PARENT_CONTROL), checked(lock / "CohortChild.SLDPRT", PART_CONTROL))
    require(control["name"] == "A18PlaneDistance" and control["split"] == "discovery" and
            len(prediction["tree"]["parent"]) == len(prediction["tree"]["child"]) == 25,
            "the SDK pair requires its actual predicted features and a disclosed A18 control")
    return fixture, prediction, paths, control, source


def generated_case(prediction):
    def placement_transform(row):
        return occurrence(row)[1]

    raw = prediction["initial"]["occurrence_transforms"]
    placements = [{"axis": "z", "angle_deg": 0.0, "translation_m": row[9:12]} for row in raw]
    require([placement_transform(row) for row in placements] == raw, "the generated case requires its authored identity rotations")
    endpoints = prediction["ordered_endpoints"]
    require([row["occurrence"] for row in endpoints] == ["SdkDatumPlateAlpha-1", "SdkDatumPlateAlpha-2"]
            and all(row["datum_type"] == "RefPlane" for row in endpoints), "the ordered child datum ownership differs")
    mate = {"kind": "distance", "name": prediction["edit"]["parameter"].split("@")[1],
            "planes": [[index, row["datum"]] for index, row in enumerate(endpoints)],
            "distance_m": prediction["initial"]["mate_distance_m"]}
    case = {"name": "SdkDistanceXAlpha", "split": "discovery", "fixed_occurrence": 0, "placements": placements, "mates": [mate]}
    edit = predict_edit(case, prediction["edit"]["new_value_m"], placement_transform)
    require([placement_transform(row) for row in edit["placements"]] == prediction["edited"]["occurrence_transforms"],
            "the independent distance edit changes a different occurrence")
    return case, edit


def observe(author, model, child, prediction):
    configurations = []
    for target, key in ((model, "assembly_configuration"), (child, "child_configuration")):
        active = author.get(target, "GetActiveConfiguration")
        name = str(author.get(active, "Name"))
        require(name == prediction[key], "a linked document changed its intended active configuration")
        configurations.append(name)
    dimensions = {}
    for name, expected in prediction["child_parameters_m"].items():
        parameter = author.get(child, "Parameter", name)
        if expected is None:
            require(parameter is None, "an extra child sketch dimension was created")
        else:
            require(parameter is not None and author.get(parameter, "DrivenState") == 2 and not author.get(parameter, "ReadOnly"),
                    "the generated child lost its live depth dimension")
            dimensions[name] = float(author.get(parameter, "SystemValue"))
            author.rec.close_number(name, dimensions[name], expected)
    return {"configurations": configurations, "child_d1": dimensions}


def state_matches(value, expected, prediction):
    for key, role in (("tree", "parent"), ("child_tree", "child")):
        actual = [[node["name"], node["type"], node["parent"]] for node in value[key]]
        if actual != prediction["tree"][role] or any(node["suppressed"] for node in value[key]):
            return False
    return (value["body_count"] == expected["body_count"] and
            [row["fixed"] for row in value["occurrences"]] == expected["fixed_flags"] and
            [row["configuration"] for row in value["occurrences"]] == [prediction["child_configuration"]] * 2 and
            len(value["mates"]) == 1 and value["mates"][0]["dimension_name"] == prediction["edit"]["full_name"] and
            math.isclose(value["mates"][0]["dimension_m"], expected["mate_distance_m"], rel_tol=2e-7) and
            all(math.isclose(value["mass"][key], expected["assembly"][key], rel_tol=2e-7, abs_tol=1e-15)
                for key in ("volume", "area")) and
            all(math.isclose(a, b, rel_tol=2e-7, abs_tol=1e-15) for a, b in zip(value["mass"]["com"], expected["assembly"]["com"], strict=True)))


def run(packet, sha):
    require(os.name == "nt", "native assembly measurement requires the pinned Windows guest")
    fixture, prediction, paths, control, source = verify(packet, sha)
    case, edit = generated_case(prediction)
    output = packet.parent / "Inspection"
    output.mkdir()
    phases = {}
    summary = {"schema": SCHEMA, "packet_sha256": sha, "phases": phases, "heldout_inputs_read": 0, "passed": False}
    control_job = {"case": control, "child_size_m": [0.04, 0.02, 0.01]}
    size = [prediction["child_dimensions_m"][key] for key in ("width", "height", "depth")]
    job = {"case": case, "child_size_m": size, "edit_distance_m": prediction["edit"]["new_value_m"]}
    parent, child = (Path(paths[name][1]) for name in ("assembly", "child"))

    def checkpoint():
        write_json(output / "Result.json", summary)

    def checked_options(author, live, part):
        return observe(author, live, part, prediction)

    def record(role, chosen_job, edit_case, assembly_path, child_path, **kw):
        phases[role] = phase(chosen_job, edit_case, role, assembly_path, child_path, output / role, **kw)
        checkpoint()
        return phases[role]

    try:
        before = record("ControlBefore", control_job, control, *source)
        if before["passed"]:
            for original, path, artifact_sha in paths.values():
                target = Path(path)
                target.parent.mkdir(exist_ok=True)
                with original.open("rb") as incoming, target.open("xb") as copied:
                    copyfileobj(incoming, copied)
                require(digest(target) == artifact_sha, "staged SDK bytes differ before native open")
            first = record("Generated", job, edit, parent, child, editing=True, observe=checked_options)
            if first["passed"]:
                final = record("FreshReopen", job, edit, parent, child, reopened=first["saved"], observe=checked_options)
                wanted = prediction["initial"]
                changed = prediction["edited"]
                summary["exact_prediction"] = (
                    all(state_matches(first[key], wanted, prediction) for key in ("initial", "rebuilt"))
                    and state_matches(first["edited"], changed, prediction) and final["passed"]
                    and all(state_matches(final[key], changed, prediction) for key in ("initial", "rebuilt"))
                    and signature(first["edited"]) == signature(final["rebuilt"])
                )
    except Exception as error:
        summary["error"] = repr(error)
    finally:
        after = record("ControlAfter", control_job, control, *source)
        verified, _, _, _, _ = verify(packet, sha)
        controls = phases.get("ControlBefore", {}).get("passed") and after["passed"]
        if controls:
            controls = signature(phases["ControlBefore"]["rebuilt"]) == signature(after["rebuilt"])
        births = {row["oracle_identity"]["process_creation_filetime"] for row in phases.values() if row.get("oracle_identity")}
        summary.update(controls_healthy=bool(controls), frozen_inputs_unchanged=verified == fixture, distinct_processes=len(births))
        summary["passed"] = bool(controls and summary["frozen_inputs_unchanged"] and summary.get("exact_prediction")
                                 and len(phases) == len(births) == 4 and all(row["passed"] for row in phases.values()))
        checkpoint()
    return summary


def main():
    parser = argparse.ArgumentParser(description="Measure a complete SDK single-distance assembly through native editing")
    parser.add_argument("command", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    packet = args.packet.resolve(strict=True)
    if args.command == "verify":
        _, prediction, _, _, _ = verify(packet, args.packet_sha256)
        generated_case(prediction)
        print('{"passed": true, "processes_started": 0}')
        return 0
    report = run(packet, args.packet_sha256)
    print(json.dumps({key: report[key] for key in ("passed", "controls_healthy", "distinct_processes")}, sort_keys=True))
    return 0 if report["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
