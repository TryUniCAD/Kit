from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PureWindowsPath
from shutil import copyfile
import sys

from AuthorCurves import digest, require, write_json
from InspectCombinedPlanarMates import ORACLE, TOOLS as BASE_TOOLS, phase, signature
from SdkPlanarGroupPrediction import predict, state_matches


SCHEMA = "kit.sw2026.sdk-explicit-planar-group-native.v1"
TOOLS = (*BASE_TOOLS, "PrepareDimensionedAssemblyPredictions.py", "InspectSdkSingleMate.py", "PrepareSdkAssemblyNative.py", "SdkPlanarGroupPrediction.py", Path(__file__).name)
CONTROL_PARENT = "fac5708432e569e787dfc00aa87fe08e5ef2d6830ec88f2d69525f8030d9fd1f"
CONTROL_CHILD = "b46e1e0f066db55730ce765cb2547b97ad1416e1ea0ceaa588bb8e819f727321"


def checked(path, wanted):
    require(path.is_file() and not path.is_symlink() and digest(path) == wanted, "a frozen explicit-group input differs: " + path.name)
    return path


def locator(row):
    return Path(row["windows_path"] if os.name == "nt" else row["host_path"])


def verify(path, sha):
    root = path.parent
    job = json.loads(checked(path, sha).read_bytes())
    require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE and job["heldout_inputs_read"] == 0 and job["native_acceptance"] is False, "expected the disclosed SDK explicit-group packet")
    require(Path(__file__).resolve().parent == (root / "Tools").resolve(strict=True) and set(job["tools_sha256"]) == set(TOOLS), "use the exact frozen explicit-group observer tools")
    for name, wanted in job["tools_sha256"].items():
        checked(root / "Tools" / name, wanted)
    fixture = json.loads(checked(root / "Fixture.json", job["fixture_sha256"]).read_bytes())
    request = json.loads(checked(root / "NeutralRequest.json", fixture["request_sha256"]).read_bytes())
    expected = json.loads(checked(root / "Prediction.json", fixture["prediction_sha256"]).read_bytes())
    require(predict(request, expected["case"], expected["edit_distance_m"]) == expected, "the independent native prediction differs from the authored neutral group")
    checked(root / "SourceManifest.json", fixture["source_manifest_sha256"])
    proof = json.loads(checked(root / "SourceProcessResult.json", fixture["source_process_result_sha256"]).read_bytes())
    require(proof["passed"] and proof["source_manifest_sha256"] == fixture["source_manifest_sha256"] and len(proof["positive_cases"]) == 6 and len(proof["prior_flat_bundles"]) == 30 and len(proof["prior_nested_bundles"]) == 2, "the full frozen SDK group proof is incomplete")
    builds = [json.loads(checked(root / (name + ".stdout"), fixture["phase_sha256"][name]).read_bytes()) for name in ("BuildA", "BuildB", "Counterpart")]
    a, b = dict(builds[0]), dict(builds[1])
    require(a.pop("worker_pid") != b.pop("worker_pid") and a == b and builds[2]["same_as_independent_research"], "the native group lacks deterministic independent construction")
    paths = {}
    for key, row in fixture["files"].items():
        source = checked(root / "FrozenGenerated" / row["file"], row["sha256"])
        native = PureWindowsPath(row["encoded_path"])
        require(source.stat().st_size == row["bytes"] and native.name == row["file"] and native.is_absolute() and row["sha256"] == builds[0][key]["sha256"], "native staging differs from the actual complete SDK bundle")
        paths[key] = source, Path(native), row["sha256"]
    control = json.loads(checked(root / "ControlCase.json", job["control_case_sha256"]).read_bytes())
    require(control["case"]["name"] == "A22CombinedRotated" and control["case"]["split"] == "discovery" and control["child_size_m"] == [.04, .02, .01], "the bracket must use the independently authored disclosed A22 profile")
    sources = checked(locator(job["control"]["parent"]), CONTROL_PARENT), checked(locator(job["control"]["child"]), CONTROL_CHILD)
    require(not any(name == "Swapp" or name == "pythoncom" or name.startswith("win32com") for name in sys.modules) if os.name != "nt" else True, "host verification imported COM")
    return fixture, expected, paths, control, sources


def observe_options(author, model, child, expected):
    import Swapp
    from AssemblyMateEvidence import mate_features
    from InspectSdkSingleMate import observe

    result = observe(author, model, child, expected)
    assembly = author.typed(model, "AssemblyDoc")
    components = {str(author.get(value, "Name2")): author.typed(value, "Component2") for value in author.get(assembly, "GetComponents", True)}
    require(set(components) == set(expected["occurrence_names"]), "the native endpoint observer has a different actual component set")
    features = list(mate_features(author, model))
    require(len(features) == len(expected["case"]["mates"]), "the native endpoint observer has an incomplete mate sequence")
    observations = result["ordered_reference_diagnostics"] = []
    for feature, spec in zip(features, expected["case"]["mates"], strict=True):
        require(str(author.get(feature, "Name")) == spec["name"], "the reference observer changed mate order")
        mate = author.typed(author.get(feature, "GetSpecificFeature2"), "Mate2")
        row = {"mate": spec["name"], "entities": []}
        observations.append(row)
        for index, (participant, datum) in enumerate(spec["planes"]):
            entity = author.typed(author.get(mate, "MateEntity", index), "MateEntity2")
            component = author.typed(author.get(entity, "ReferenceComponent"), "Component2")
            name = str(author.get(component, "Name2"))
            require(name == expected["occurrence_names"][participant] and int(author.get(entity, "ReferenceType2")) == 4, "native mate reference changed its exact occurrence or principal datum type")
            reference, repeated = author.get(entity, "Reference"), author.get(entity, "Reference")
            feature = author.get(components[name], "FeatureByName", datum)
            require(feature is not None and author.get(feature, "GetTypeName2") == "RefPlane", "the selected component has no actual named principal plane")
            specific, again = author.get(feature, "GetSpecificFeature2"), author.get(feature, "GetSpecificFeature2")
            reference_equal = int(author.rec.call("IsSame repeated group reference", Swapp.invoke, author.app, "IsSame", reference, repeated))
            specific_equal = int(author.rec.call("IsSame repeated group specific plane", Swapp.invoke, author.app, "IsSame", specific, again))
            canonical_equal = int(author.rec.call("IsSame diagnostic group reference and named specific plane", Swapp.invoke, author.app, "IsSame", reference, specific))
            require(reference_equal == specific_equal == 1 and canonical_equal in (0, 1), "the matched native reference positive controls are invalid")
            row["entities"].append({"occurrence": name, "datum": datum, "reference_type": 4, "repeated_reference_equality": reference_equal,
                                    "repeated_specific_plane_equality": specific_equal, "specific_plane_equality_diagnostic": canonical_equal})
    return result


def run(path, sha):
    require(os.name == "nt", "only the serial pinned Windows oracle can measure an explicit group")
    fixture, expected, paths, control, source = verify(path, sha)
    output = path.parent / "Inspection"
    output.mkdir()
    rows = {}
    report = {"schema": SCHEMA, "packet_sha256": sha, "fixture_sha256": digest(path.parent / "Fixture.json"), "source_manifest_sha256": fixture["source_manifest_sha256"], "phases": rows, "heldout_inputs_read": 0, "passed": False}
    job = {"case": expected["case"], "child_size_m": [expected["child_dimensions_m"][key] for key in ("width", "height", "depth")], "edit_distance_m": expected["edit_distance_m"]}
    targets = tuple(paths[key][1] for key in ("assembly", "child"))
    control_expected = {"case": control["case"], "assembly_configuration": "Default", "child_configuration": "Default",
                        "child_parameters_m": {"D1@Sketch1": .04, "D2@Sketch1": .02, "D1@Boss-Extrude1": .01},
                        "occurrence_names": ["CohortChild-" + str(index + 1) for index in range(len(control["case"]["placements"]))]}
    control_options = {"observe": lambda author, model, child: observe_options(author, model, child, control_expected)}

    def record(role, selected, edit, chosen, **options):
        rows[role] = phase(selected, edit, role, *chosen, output / role, **options)
        write_json(output / "Result.json", report)
        return rows[role]

    try:
        before = record("ControlBefore", control, control["case"], source, **control_options)
        if before["passed"]:
            for original, native, wanted in paths.values():
                native.parent.mkdir(exist_ok=True)
                with original.open("rb") as incoming, native.open("xb") as target:
                    target.write(incoming.read())
                require(digest(native) == wanted, "the SDK native working input changed before open")
            options = {"observe": lambda author, model, child: observe_options(author, model, child, expected)}
            first = record("Generated", job, expected["edited_case"], targets, editing=True, **options)
            if first["passed"]:
                reopened = record("FreshReopen", job, expected["edited_case"], targets, reopened=first["saved"], **options)
                report["exact_prediction"] = bool(all(state_matches(first[key], expected["initial"], expected) for key in ("initial", "rebuilt")) and state_matches(first["edited"], expected["edited"], expected) and all(state_matches(reopened[key], expected["edited"], expected) for key in ("initial", "rebuilt")))
                report["edit_identity_preserved"] = signature(first["rebuilt"]) == signature(first["edited"])
                report["reopen_identity_preserved"] = signature(first["edited"]) == signature(reopened["rebuilt"])
    except Exception as error:
        report["error"] = repr(error)
    finally:
        after = record("ControlAfter", control, control["case"], source, **control_options)
        checked_fixture = verify(path, sha)[0]
        healthy = bool(rows.get("ControlBefore", {}).get("passed") and after["passed"])
        report["controls_healthy"] = healthy
        report["control_identity_preserved"] = bool(healthy and signature(rows["ControlBefore"]["rebuilt"]) == signature(after["rebuilt"]))
        report["frozen_inputs_unchanged"] = fixture == checked_fixture
        report["distinct_processes"] = len({row["oracle_identity"]["process_creation_filetime"] for row in rows.values() if row.get("oracle_identity")})
        report["passed"] = bool(report["control_identity_preserved"] and report["frozen_inputs_unchanged"] and report.get("exact_prediction") and report.get("edit_identity_preserved") and report.get("reopen_identity_preserved") and len(rows) == report["distinct_processes"] == 4 and all(row["passed"] for row in rows.values()))
        write_json(output / "Result.json", report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    path = args.packet.resolve(strict=True)
    if args.command == "verify":
        verify(path, args.packet_sha256)
        print('{"passed": true, "native_processes_started": 0}')
        return 0
    result = run(path, args.packet_sha256)
    print(json.dumps({key: result[key] for key in ("passed", "controls_healthy", "distinct_processes")}, sort_keys=True))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
