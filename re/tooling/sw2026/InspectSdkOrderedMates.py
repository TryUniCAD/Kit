from __future__ import annotations

import argparse
import json
from itertools import islice
import os
from pathlib import Path, PureWindowsPath
from shutil import copyfileobj
import sys

from AuthorCurves import digest, require, write_json
from InspectCombinedPlanarMates import ORACLE, phase, signature
from InspectSdkSingleMate import TOOLS as SINGLE_TOOLS, observe
from PlanarMateEdit import check_satisfied
from SdkOrderedMateExpectations import KINDS, placement_transform, state_matches, verify_predictions


SCHEMA = "kit.sw2026.sdk-ordered-mates-native-trial.v1"
TOOLS = (*SINGLE_TOOLS, "PrepareSdkAssemblyNative.py", "SdkOrderedMateExpectations.py", "PrepareSdkOrderedMateTrial.py", Path(__file__).name)
CONTROL_PARENT = "fac5708432e569e787dfc00aa87fe08e5ef2d6830ec88f2d69525f8030d9fd1f"
CONTROL_CHILD = "b46e1e0f066db55730ce765cb2547b97ad1416e1ea0ceaa588bb8e819f727321"


def checked(path, expected):
    path = path.resolve(strict=True)
    require(path.is_file() and digest(path) == expected, "a frozen ordered-mate input changed: " + path.name)
    return path


def control_paths(job):
    key = "windows_path" if os.name == "nt" else "host_path"
    return tuple(checked(Path(job["control"][name][key]), expected) for name, expected in (("parent", CONTROL_PARENT), ("child", CONTROL_CHILD)))


def verify(packet, expected):
    root = packet.parent.resolve(strict=True)
    job = json.loads(checked(packet, expected).read_bytes())
    require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE and job["heldout_inputs_read"] == 0,
            "expected the exact disclosed SDK ordered-mate trial")
    tools = (root / "Tools").resolve(strict=True)
    require(Path(__file__).resolve().parent == tools and set(job["tools_sha256"]) == set(TOOLS), "ordered observer source closure differs")
    for name, value in job["tools_sha256"].items():
        checked(tools / name, value)
    fixture = json.loads(checked(root / "Fixture.json", job["fixture_sha256"]).read_bytes())
    require(fixture["schema"] == "kit.sw2026.sdk-ordered-native-fixture.v1" and fixture["heldout_inputs_read"] == 0
            and fixture["typed_stream_round_trips"] == 22 and fixture["independent_composer_matches"],
            "the independently generated ordered fixture is incomplete")
    prediction = json.loads(checked(root / "Prediction.json", fixture["prediction_sha256"]).read_bytes())
    request = json.loads(checked(root / "NeutralRequest.json", fixture["request_sha256"]).read_bytes())
    checked(root / "SourceManifest.json", fixture["source_manifest_sha256"])
    proof = json.loads(checked(root / "SourceProcessResult.json", fixture["source_process_result_sha256"]).read_bytes())
    require(proof["passed"] and proof["source_manifest_sha256"] == fixture["source_manifest_sha256"]
            and proof["heldout_inputs_read"] == 0, "the frozen writer process qualification differs")
    reports = {}
    for name, value in fixture["phase_sha256"].items():
        reports[name] = json.loads(checked(root / (name + ".stdout"), value).read_bytes())
        require(reports[name]["passed"] and reports[name]["runtime_input_file_reads"] == 0, "guarded ordered construction failed")
    first, second = (dict(reports[name]) for name in ("BuildA", "BuildB"))
    require(first.pop("worker_pid") != second.pop("worker_pid") and first == second, "the ordered fixture must reproduce in separate processes")
    require(set(fixture["files"]) == {"SdkOrderedMixed.SLDASM", "SdkDatumPlateBeta.SLDPRT"}, "unexpected generated ordered pair")
    paths = {}
    for name, row in fixture["files"].items():
        path = checked(root / "FrozenGenerated" / name, row["sha256"])
        native = PureWindowsPath(row["encoded_path"])
        kind = "assembly" if native.suffix.upper() == ".SLDASM" else "child"
        require(native.is_absolute() and native.name == name and path.stat().st_size == row["bytes"]
                and reports["BuildA"][kind]["sha256"] == row["sha256"], "the generated ordered pair or encoded path differs")
        paths[kind] = path, native, row["sha256"]
    require(paths["assembly"][1].parent == paths["child"][1].parent, "the generated ordered pair must share its actual encoded directory")
    control = json.loads(checked(root / "ControlCase.json", job["control_case_sha256"]).read_bytes())
    require(control["case"]["split"] == "discovery" and len(control["case"]["mates"]) == 3
            and [row["kind"] for row in control["case"]["mates"]] == ["parallel", "distance", "coincident"],
            "expected the qualified disclosed A22 rotated control")
    check_satisfied(control["case"]["mates"], [placement_transform(row) for row in control["case"]["placements"]])
    require(all(value > 0 for value in control["child_size_m"]) and len(control["child_size_m"]) == 3,
            "the control must retain its separate authored child geometry")
    for name, value in (("parent", CONTROL_PARENT), ("child", CONTROL_CHILD)):
        require(job["control"][name]["sha256"] == value and PureWindowsPath(job["control"][name]["windows_path"]).is_absolute(),
                "the exact qualified control identity differs")
    source = control_paths(job)
    case, edit = verify_predictions(request, prediction)
    return fixture, prediction, paths, control, source, case, edit


def observe_ordered(author, model, child, prediction):
    import Swapp
    from AssemblyMateEvidence import mate_features

    result = observe(author, model, child, prediction)
    features = list(islice(mate_features(author, model), 4))
    require(len(features) == 3, "the native ordered group must contain exactly three mate features")
    references = result["ordered_native_references"] = []
    for feature, expected in zip(features, prediction["ordered_endpoints"], strict=True):
        require(author.get(feature, "Name") == expected["mate"] and author.get(feature, "GetTypeName2") == KINDS[expected["kind"]][1]
                and not author.get(feature, "IsSuppressed"), "the native ordered mate name, type or suppression differs")
        mate = author.typed(author.get(feature, "GetSpecificFeature2"), "Mate2")
        require(author.get(mate, "GetMateEntityCount") == 2, "the native ordered mate requires exactly two endpoints")
        endpoints = []
        for index, (name, datum) in enumerate(zip(expected["occurrences"], expected["datums"], strict=True)):
            entity = author.typed(author.get(mate, "MateEntity", index), "MateEntity2")
            component = author.typed(author.get(entity, "ReferenceComponent"), "Component2")
            document = author.get(component, "GetModelDoc2")
            require(author.get(component, "Name2") == name and author.get(entity, "ReferenceType2") == 4
                    and document is not None and Path(author.get(document, "GetPathName")).samefile(Path(author.get(child, "GetPathName"))),
                    "a native ordered mate endpoint changed its occurrence or resolved child")
            named = author.get(component, "FeatureByName", datum)
            require(named is not None and author.get(named, "GetTypeName2") == "RefPlane", "the endpoint's authored datum feature is unavailable")
            reference, plane = Swapp.cv(entity, "Reference"), Swapp.cv(named, "GetSpecificFeature2")
            require(reference is not None and plane is not None, "the endpoint did not resolve both specific plane objects")
            equality = int(Swapp.invoke(author.app, "IsSame", reference, plane))
            endpoints.append({"occurrence": name, "datum": datum, "reference_type": 4, "specific_plane_equality": equality})
            require(equality == 1, "the native mate reference differs from the exact occurrence's specific principal plane")
        references.append({"mate": expected["mate"], "kind": expected["kind"], "entities": endpoints})
    return result


def run(packet, expected):
    require(os.name == "nt", "native ordered measurement requires the pinned Windows guest")
    fixture, prediction, paths, control, source, case, edit = verify(packet, expected)
    output = packet.parent / "Inspection"
    output.mkdir()
    phases = {}
    summary = {"schema": SCHEMA, "packet_sha256": expected, "fixture_sha256": digest(packet.parent / "Fixture.json"),
               "phases": phases, "heldout_inputs_read": 0, "passed": False}
    job = {"case": case, "child_size_m": [prediction["child_dimensions_m"][key] for key in ("width", "height", "depth")],
           "edit_distance_m": prediction["edit"]["new_value_m"]}
    parent, child = (Path(paths[name][1]) for name in ("assembly", "child"))

    def checkpoint():
        write_json(output / "Result.json", summary)

    def options(author, live, part):
        return observe_ordered(author, live, part, prediction)

    def record(role, chosen_job, edit_case, assembly_path, child_path, **extra):
        phases[role] = phase(chosen_job, edit_case, role, assembly_path, child_path, output / role, **extra)
        checkpoint()
        return phases[role]

    try:
        before = record("ControlBefore", control, control["case"], *source)
        if before["passed"]:
            for original, native, artifact_sha in paths.values():
                target = Path(native)
                target.parent.mkdir(parents=True, exist_ok=True)
                with original.open("rb") as incoming, target.open("xb") as outgoing:
                    copyfileobj(incoming, outgoing)
                require(digest(target) == artifact_sha, "the actual encoded generated input changed before native open")
            first = record("Generated", job, edit, parent, child, editing=True, observe=options)
            if first["passed"]:
                final = record("FreshReopen", job, edit, parent, child, reopened=first["saved"], observe=options)
                summary["exact_prediction"] = bool(final["passed"] and
                    all(state_matches(first[key], prediction["initial"], prediction) for key in ("initial", "rebuilt")) and
                    state_matches(first["edited"], prediction["edited"], prediction) and
                    all(state_matches(final[key], prediction["edited"], prediction) for key in ("initial", "rebuilt")))
                summary["edit_identity_preserved"] = signature(first["rebuilt"]) == signature(first["edited"])
                summary["reopen_identity_preserved"] = bool(final["passed"] and signature(first["edited"]) == signature(final["rebuilt"]))
    except Exception as error:
        summary["error"] = repr(error)
    finally:
        after = record("ControlAfter", control, control["case"], *source)
        verified, *_ = verify(packet, expected)
        controls = bool(phases.get("ControlBefore", {}).get("passed") and after["passed"])
        summary["controls_healthy"] = controls
        summary["source_bracket_identity"] = bool(controls and signature(phases["ControlBefore"]["rebuilt"]) == signature(after["rebuilt"]))
        births = {row["oracle_identity"]["process_creation_filetime"] for row in phases.values() if row.get("oracle_identity")}
        summary.update(frozen_inputs_unchanged=verified == fixture, distinct_processes=len(births))
        summary["passed"] = bool(summary["source_bracket_identity"] and summary["frozen_inputs_unchanged"] and summary.get("exact_prediction")
                                 and summary.get("edit_identity_preserved") and summary.get("reopen_identity_preserved")
                                 and len(phases) == len(births) == 4 and all(row["passed"] for row in phases.values()))
        checkpoint()
    return summary


def main():
    parser = argparse.ArgumentParser(description="Measure a fully SDK generated ordered planar group with immutable A22 brackets")
    parser.add_argument("command", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    packet = args.packet.resolve(strict=True)
    if args.command == "verify":
        verify(packet, args.packet_sha256)
        forbidden = [name for name in sys.modules if name == "Swapp" or name == "pythoncom" or name.startswith(("win32com", "win32api", "win32process"))]
        require(not forbidden, "the pure host preflight imported a native COM dependency")
        print(json.dumps({"passed": True, "native_processes_started": 0, "com_imports": forbidden}, sort_keys=True))
        return 0
    report = run(packet, args.packet_sha256)
    print(json.dumps({key: report[key] for key in ("passed", "controls_healthy", "distinct_processes")}, sort_keys=True))
    return 0 if report["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
