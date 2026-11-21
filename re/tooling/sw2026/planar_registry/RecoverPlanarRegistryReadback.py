from argparse import ArgumentParser
from hashlib import sha256
import json
from math import isclose
import os
from pathlib import Path
from subprocess import DEVNULL, PIPE, Popen, TimeoutExpired
import sys


SCHEMA = "kit.sw2026.disclosed-planar-registry-readback-recovery.v1"
FIRST = "8efd93beb3f017240bd6eb1ab27678fcef1f21252023fc38180853dfd62951a4"
FIXTURE = "33d6f617549610329ef93badc5ec163264de7a5a5440d9f4bb29c09a09ff5160"
CONTROL = "d932660fd055e80c12c1fa3fce4413083b9e21fd36104a47b6dba6afc92ff35e"
RECIPE = "4363a20d3ff5c2d71eda6b3fea213bfe3f54294317848012eed93fd6f8191df1"
OBSERVER = "2685b650ff596fd6ba689f658f508d3748b436251c31f2ba6535c8e88a00db8f"
TOOLS = Path("re/tooling/sw2026")
PLANAR = TOOLS / "planar_registry"
STEPS = ("before", "generated", "reopen", "after")
SAVED = {
    "PublicPlanarPair2.SLDASM": "ab1164708763381c3498ad8bc7b6841a09823f94bf52038685f67ad61902af56",
    "PublicDatumPrism.SLDPRT": "670d8a2fb9c9c03a643dceceb5ac35ce9c1c6095ba7384a08b48b0b710dc1702",
}
STREAMS = {
    "Contents/CMgr", "Contents/CMgrHdr2", "Contents/Config-0",
    "Contents/Config-0-ModelHeader", "Contents/Config-0-ResolvedFeatures", "Header2",
}
FAILURE = "ValueError('public native read imported a CAD runtime dependency')"


def require(value, message):
    if not value:
        raise ValueError(message)


def fingerprint(data):
    return sha256(data).hexdigest()


def checked(path, digest):
    require(path.is_file() and not path.is_symlink(), "required regular file unavailable: " + path.name)
    raw = path.read_bytes()
    require(fingerprint(raw) == digest, "required input digest differs: " + path.name)
    return raw


def bind_packet(root):
    fixture = json.loads(checked(root / "Fixture.json", FIXTURE))
    control = json.loads(checked(root / "ControlBinding.json", CONTROL))
    first = json.loads(checked(root / "Inspection/Summary.json", FIRST))
    recipe = json.loads(checked(root / "Recipe.json", RECIPE))
    require(first == {
        "schema": fixture["schema"], "fixture_sha256": FIXTURE, "control_sha256": CONTROL,
        "missing_phases": [], "native_process_count": 4, "controls_healthy": True,
        "ordered_distinct_lifetimes": True, "trees_and_owners_retained": False, "passed": False,
        "phase_sha256": first["phase_sha256"], "new_heldout_credit": 0,
    } and recipe["order"] == list(STEPS) and recipe["run_after_even_on_failure"] is True
       and recipe["fixture_sha256"] == control["fixture_sha256"] == FIXTURE and recipe["control_sha256"] == CONTROL
       and set(first["phase_sha256"]) == set(STEPS), "require the exact original failed disclosed packet")
    code = root / "CodeRoot"
    manifest = json.loads(checked(root / "CodeManifest.json", fixture["code_manifest_sha256"]))
    for name in ("ObservePlanarRegistry.py", "PlanarRegistryBuild.py"):
        path = PLANAR / name
        checked(code / path, OBSERVER if name == "ObservePlanarRegistry.py" else manifest["files"][path.as_posix()])
    sys.path[:0] = [str(code / PLANAR), str(code / TOOLS)]
    from ObservePlanarRegistry import verify

    frozen, prediction, _, verified_code = verify(root, FIXTURE)
    require(verified_code == code and frozen == fixture, "the frozen SDK fixture or path changed")
    return fixture, control, first, prediction, code


def capture_phase(root, role, wanted, expected_input, edit_m):
    folder = root / "Inspection" / role
    phase = json.loads(checked(folder / "Phase.json", wanted))
    native = phase["native_record"]
    digest = native["record_sha256"]
    record = json.loads(checked(folder / "Record.json", digest))
    checks = record["checks"]
    require(phase["role"] == native["role"] == role and phase["fixture_sha256"] == FIXTURE
            and phase["control_sha256"] == CONTROL and record["job"] == {"role": role, "input": expected_input}
            and record["passed"] is native["passed"] is True and not record["cleanup_errors"]
            and record["first_failure"] is None and bool(checks) and all(row["passed"] is True for row in checks)
            and native == {**record["result"], "record_sha256": digest, "numeric_checks": len(checks)}
            and native["open_errors"] == native["open_warnings"] == 0 and not native["dialogs"]
            and not native["controller_diagnostics"],
            "native phase or paired raw receipt failed: " + role)
    if role == "reopen":
        require(phase["passed"] is False and phase["postflight_error"] == FAILURE and "saved_postflight" not in phase,
                "fresh reopen has another first failure")
    else:
        require(phase["passed"] is True and "postflight_error" not in phase,
                "a prior native phase failed: " + role)
    calls = {name: [(index, item) for index, item in enumerate(record["api_calls"]) if item["method"] == name]
             for name in ("verify idle combined-mate oracle", "start fresh combined-mate oracle",
                          "verify exact combined-mate oracle", "open exact paired native assembly", "ForceRebuild3",
                          "SetSystemValue3", "persist owned child before parent", "persist generated parent after its child")}
    opened, = [item for _, item in calls["open exact paired native assembly"]]
    rebuilds = [item["result"] for _, item in calls["ForceRebuild3"]]
    edits, child_save, parent_save = (calls[key] for key in ("SetSystemValue3", "persist owned child before parent",
                                                           "persist generated parent after its child"))
    require(all(len(calls[key]) == 1 for key in ("verify idle combined-mate oracle",
                                                 "start fresh combined-mate oracle", "verify exact combined-mate oracle"))
            and opened["result"][1:] == [0, 0] and opened["keyword_arguments"]["read_only"] is (role != "generated")
            and rebuilds == ([True, True] if role == "generated" else [True]),
            "native process, actual open or rebuild contract differs: " + role)
    if role == "generated":
        (edit_index, edit), = edits
        (child_index, child), = child_save
        (parent_index, parent), = parent_save
        require(calls["ForceRebuild3"][0][0] < edit_index < calls["ForceRebuild3"][1][0] < child_index < parent_index
                and edit["arguments"]["values"][:2] == [edit_m, 1]
                and edit["result"] == native["edit_status"] == 0
                and child["result"] is parent["result"] is True, "actual edit and child-first save order differ")
    else:
        require(not (edits or child_save or parent_save), "a read-only phase edited or saved its input")
    return phase, record["com_type_library"], digest, len(checks)


def observed_options(state, expected):
    require(state["configurations"] == expected["configurations"]
            and state["child_d1"].keys() == expected["dimensions"].keys()
            and all(isclose(value, expected["dimensions"][key], rel_tol=2e-7, abs_tol=1e-12)
                    for key, value in state["child_d1"].items()), "native configuration or child driving dimensions changed")
    for row, mate in zip(state["ordered_reference_diagnostics"], expected["case"]["mates"], strict=True):
        require(row["mate"] == mate["name"], "native ordered reference diagnostics changed mate")
        for entity, (slot, datum) in zip(row["entities"], mate["planes"], strict=True):
            require((entity["occurrence"], entity["datum"]) == (expected["occurrences"][slot], datum)
                    and entity["reference_type"] == 4 and entity["repeated_reference_equality"] == 1
                    and entity["repeated_specific_plane_equality"] == 1
                    and entity["specific_plane_equality_diagnostic"] in (0, 1),
                    "native diagnostic lost actual selected child datum or its owner")


def validate_lifecycle(root, fixture, control, first, prediction):
    from InspectCombinedPlanarMates import ORACLE, signature
    from SdkPlanarGroupPrediction import state_matches

    parent, child = SAVED
    initial = {role: fixture["files"][name]["sha256"] for role, name in (("parent", parent), ("child", child))}
    saved = {"parent": SAVED[parent], "child": SAVED[child]}
    bracket = dict(zip(("parent", "child"), control["file_sha256"], strict=True))
    inputs = {"before": bracket, "generated": initial, "reopen": saved, "after": bracket}
    control_spec = control["case"]
    control_options = {"case": control_spec, "configurations": ["Default", "Default"],
                       "dimensions": {"D1@Sketch1": .04, "D2@Sketch1": .02, "D1@Boss-Extrude1": .01},
                       "occurrences": [f"CohortChild-{index + 1}" for index in range(len(control_spec["placements"]))]}
    candidate_options = {"case": prediction["case"],
                         "configurations": [prediction["assembly_configuration"], prediction["child_configuration"]],
                         "dimensions": prediction["child_parameters_m"], "occurrences": prediction["occurrence_names"]}
    records, reports, signatures = {}, {}, {}
    for role in STEPS:
        phase, library, raw_sha, count = capture_phase(
            root, role, first["phase_sha256"][role], inputs[role], prediction["edit_distance_m"])
        native = phase["native_record"]
        records[role] = native
        identity = native["oracle_identity"]
        lifetime = identity["process_creation_filetime"]
        created = (lifetime - 116444736000000000) / 10000000
        require(identity["sha256"] == ORACLE and identity["version_matches"] is True
                and identity["file_version"] == "34.5.2.0604" and library["major"] == 34
                and native["started_at"] <= created <= native["finished_at"], "pinned process identity differs: " + role)
        labels = ("initial", "rebuilt", "edited") if role == "generated" else ("initial", "rebuilt")
        candidate = role in ("generated", "reopen")
        signatures[role] = {}
        for label in labels:
            state = native[label]
            options = candidate_options if candidate else control_options
            observed_options(native[label + "_options"], options)
            require(state["body_count"] == len(options["occurrences"])
                    and all(row["visible_child_bodies"] == 1 for row in state["occurrences"]),
                    "native phase lost a visible actual solid: " + role + "/" + label)
            require(all(row["error"] == row["warning"] == 0 and row["suppressed"] is False
                        for row in (*state["tree"], *state["child_tree"])),
                    "native tree has a suppressed or diagnosed row: " + role + "/" + label)
            signatures[role][label] = signature(state)
            if candidate:
                basis = "edited" if role == "reopen" or label == "edited" else "initial"
                require(phase["analytic_checks"][label] is True and state_matches(state, prediction[basis], prediction),
                        "native tree, geometry, mate or edit fails independent prediction: " + role + "/" + label)
        reports[role] = {
            "record_sha256": raw_sha, "phase_sha256": first["phase_sha256"][role],
            "process_creation_filetime": lifetime, "process_id": identity["process_id"],
            "native_checks": count, "open_status": [native["open_errors"], native["open_warnings"]],
            "ordered_tree_rows": [len(native["rebuilt"][key]) for key in ("tree", "child_tree")],
            "verified_tree_and_owner_signature_sha256": fingerprint(
                json.dumps(signatures[role]["rebuilt"], sort_keys=True, separators=(",", ":")).encode()),
        }
    require(len({row["process_creation_filetime"] for row in reports.values()}) == 4
            and all(records[early]["finished_at"] <= records[later]["started_at"]
                    for early, later in zip(STEPS[:-1], STEPS[1:], strict=True)),
            "the four end-to-end native lifetimes overlap or repeat")
    require(all(value == signatures["before"]["initial"] for role in ("before", "after")
                for value in signatures[role].values()), "A22 brackets disagree on actual tree and owner identity")
    require(all(value == signatures["generated"]["initial"] for role in ("generated", "reopen")
                for value in signatures[role].values()), "generated edit or fresh reopen changes actual tree or owner identity")
    wrote, reopened = records["generated"]["saved"], records["reopen"]
    require(wrote["parent"] == saved["parent"] and wrote["child"]["native_sha256"] == saved["child"]
            and wrote["parent_status"] == wrote["child"]["save_status"] == [True, 0, 0]
            and wrote["child"]["original_sha256"] == initial["child"] and wrote["child"]["path_basename"] == child
            and wrote["child"]["update_stamp"] == reopened["child_stamp_on_open"]
            and records["generated"]["rebuilt"]["mass"]["com"] != records["generated"]["edited"]["mass"]["com"],
            "successful edit, synchronized save or actual fresh reopen lost the pinned child")
    return {
        "oracle_sha256": ORACLE, "oracle_version": "34.5.2.0604", "controls_healthy": True,
        "ordered_distinct_lifetimes": True, "tree_and_owner_signatures_retained": True,
        "native_process_count": len(reports), "native_numeric_checks": sum(row["native_checks"] for row in reports.values()),
        "phases": reports, "child_stamp_on_fresh_reopen": reopened["child_stamp_on_open"],
        "child_stamp_after_fresh_rebuild": reopened["child_stamp_after_rebuild"],
        "native_mass_and_geometry": {
            role: {label: {key: row[key] for key in ("body_count", "mass", "child_mass")}
                   for label, row in records[role].items() if label in signatures[role]}
            for role in ("generated", "reopen")
        },
    }


def read_public(code, parent):
    entry = code / TOOLS / "ReadSdkOrderedNative.py"
    with Popen((sys.executable, "-I", "-B", str(entry), "read", "--root", str(code), "--file", str(parent)),
               stdin=DEVNULL, stdout=PIPE, stderr=PIPE) as process:
        try:
            stdout, stderr = process.communicate(timeout=90)
        except TimeoutExpired:
            process.kill()
            process.communicate()
            raise
        require(process.returncode == 0, stderr.decode(errors="replace"))
        row = json.loads(stdout)
        require(row["worker_pid"] == process.pid != os.getpid() and row["com_imports"] == []
                and row["input_sha256"] == SAVED[parent.name], "strict worker identity, CAD prohibition or file binding failed")
        return row["document_json"], {
            "worker_pid": process.pid, "supervisor_pid": os.getpid(), "returncode": process.returncode,
            "interpreter_version": sys.version, "isolated_python_argv": ["-I", "-B"],
            "stdout_sha256": fingerprint(stdout), "stderr_sha256": fingerprint(stderr), "com_imports": row["com_imports"],
            "reader_sha256": fingerprint(entry.read_bytes()),
        }


def saved_readback(code, fixture, prediction, paths):
    from interchange import CadDocument
    from ReadSdkPlanarGroupNative import audit, compare
    from RectanglePresentation import differences, observe

    parent, child = paths
    result = {}
    try:
        display = observe(checked(child, SAVED[child.name]))
        predicted = fixture["actual_child_display"]
        deltas = {
            key: [{"path": row["path"], "generated": row["source"], "saved": row["generated"]}
                  for row in differences(predicted, display, absolute=tolerance)]
            for key, tolerance in (("exact_differences", 0), ("frozen_gate_discrepancies", 1e-12))
        }
        result["display"] = {"generated": predicted, "saved": display, **deltas,
                             "frozen_tolerance": 1e-12, "passed": not deltas["frozen_gate_discrepancies"]}
    except Exception as error:
        result["display"] = {"passed": False, "error": repr(error)}
    try:
        document, process = read_public(code, parent)
        result["strict_public_read_process"] = process
        result["strict_public_readback"] = compare(CadDocument.from_json(document), prediction, True, SAVED[child.name])
    except Exception as error:
        result["strict_public_readback"] = {"passed": False, "error": repr(error)}
    results = {}
    for path in (parent, child):
        try:
            replay = audit(code, path)
            streams = replay["typed_stream_round_trips"]
            names = STREAMS | {"Contents/Config-0-MatesList"} if path == parent else STREAMS
            require(replay["input_sha256"] == SAVED[path.name] and replay["passed"] is True
                    and set(streams) == names and all(row["byte_identity"] is True for row in streams.values()),
                    "saved typed linked stream identity or inventory changed: " + path.name)
            results[path.name] = {"passed": True, "streams": streams}
        except Exception as error:
            results[path.name] = {"passed": False, "error": repr(error)}
    result["typed_linked_replays"] = results
    result["typed_linked_stream_count"] = sum(len(row.get("streams", {})) for row in results.values())
    result["passed"] = result["display"]["passed"] and result["strict_public_readback"]["passed"] \
        and all(row["passed"] for row in results.values()) and result["typed_linked_stream_count"] == 13
    return result


def recover(root):
    fixture, control, first, prediction, code = bind_packet(root)
    paths = tuple(root / "GeneratedInput" / name for name in SAVED)
    for path in paths:
        checked(path, SAVED[path.name])
    native = validate_lifecycle(root, fixture, control, first, prediction)
    result = saved_readback(code, fixture, prediction, paths)
    for name, digest in (
        ("Inspection/Summary.json", FIRST), ("Fixture.json", FIXTURE), ("ControlBinding.json", CONTROL),
        ("Recipe.json", RECIPE), ("CodeManifest.json", fixture["code_manifest_sha256"]),
        ("NeutralRequest.json", fixture["request_sha256"]), ("Prediction.json", fixture["prediction_sha256"]),
        ("WorkerInput.json", fixture["worker_input_sha256"]),
        ((Path("CodeRoot") / PLANAR / "ObservePlanarRegistry.py").as_posix(), OBSERVER),
        *((f"FrozenGenerated/{name}", value["sha256"]) for name, value in fixture["files"].items()),
    ):
        checked(root / name, digest)
    for role, row in native["phases"].items():
        checked(root / "Inspection" / role / "Phase.json", row["phase_sha256"])
        checked(root / "Inspection" / role / "Record.json", row["record_sha256"])
    for path in paths:
        checked(path, SAVED[path.name])
    return {
        "schema": SCHEMA, "first_summary_sha256": FIRST, "first_summary_passed": first["passed"],
        "first_postflight_error": FAILURE, "frozen_fixture_sha256": FIXTURE, "frozen_control_sha256": CONTROL,
        "frozen_recipe_sha256": RECIPE, "frozen_observer_sha256": OBSERVER,
        "frozen_source_manifest_sha256": fixture["code_manifest_sha256"], "saved_sha256": SAVED,
        "recovery_tool_sha256": fingerprint(Path(__file__).read_bytes()), "native_lifecycle": native,
        "saved_readback": result, "input_identities_preserved": True, "native_processes_started": 0,
        "writer_output_count": 0, "prior_source_inputs_read": 0, "new_heldout_credit": 0, "passed": result["passed"],
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.packet.resolve(strict=True)
    target = args.output.resolve()
    require(not args.output.is_symlink() and not target.exists() and not target.is_relative_to(root),
            "write a new readback receipt outside the immutable original packet")
    result = recover(root)
    value = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with target.open("xb") as stream:
        stream.write(value)
    print(json.dumps({"passed": result["passed"], "receipt_sha256": fingerprint(value),
                      "native_processes_started": 0, "new_heldout_credit": 0}, sort_keys=True))
    raise SystemExit(0 if result["passed"] else 3)


if __name__ == "__main__":
    main()
