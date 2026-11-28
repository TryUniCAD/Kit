from __future__ import annotations

import argparse
import json
import os
from itertools import islice
from pathlib import Path, PureWindowsPath
from shutil import copyfileobj
import sys
import time

from AuthorCurves import Recorder, digest, require, write_json
import InspectEncodedDistanceMate as encoded
import InspectGeneratedDistanceMate as baseline
from InspectGeneratedCoincidentMate import save_owned


SCRIPT = Path(__file__).resolve()
SCHEMA = "kit.sw2026.generated-distance-mate-edit.v1"
SOURCE_TRIAL = "fc150e226e7c18467e17d73a55404e93868df1a63f870e7a00455810e37e5087"
REPLAY_RESULT = "e893156fecc8f286ff82d4564565319e23d5bfc0244e08373e586690448dd450"
REPLAY_EVIDENCE = "a8e67a0e8a8712de46500b6657a27a4ad658c69827f4877adc20af2b9ddbb8c2"
ENCODED_PARENT = encoded.ORACLE_FOLDER / "DistanceMateEditTrial01"
TOOLS = (*baseline.TOOLS, "InspectEncodedDistanceMate.py", SCRIPT.name)
ARTIFACTS = ("Request.json", "GeneratorReport.json", "WriterReceipt.json", "WriterSource.json", "PriorNativeOpen.json")
DIMENSION_DELTA = 0.01675
CURRENT_CONFIGURATION = 1
SET_VALUE_SUCCESS = 0


def admitted_evidence(root, sha):
    receipt = json.loads(baseline.checked(root / "PriorNativeOpen.json", sha, owner=root).read_bytes())
    require(sha == REPLAY_EVIDENCE and receipt["native_open_receipt_sha256"] == REPLAY_RESULT and receipt["passed"] is False
            and receipt["raw_failed_check"] == "child_dimensions" and receipt["controls_healthy"] and receipt["measured_vendor_loadable"]
            and receipt["measured_application_geometry_matches"], "unexpected prior read-only observation")
    child = receipt["child_authored_scope"]
    require(not child["authored_rectangle_dimensions"] and not any(child["sketch_dimension_record_counts"].values()) and child["sketch_display_dimension_count"] == 0,
            "prior typed child scope differs")
    return receipt


def verify(path, sha):
    root = path.parent
    baseline.checked(path, sha, owner=root)
    require(path.name == "EditTrial.json" and SCRIPT.parent == root / "Tools", "run the frozen owned edit observer")
    packet = json.loads(path.read_bytes())
    require(packet["schema"] == SCHEMA and packet["native_acceptance"] is False and packet["heldout_inputs_tested"] == 0
            and packet["source_trial_sha256"] == SOURCE_TRIAL and set(packet["tool_hashes"]) == set(TOOLS), "unexpected edit trial provenance")
    for name, tag in packet["tool_hashes"].items():
        baseline.checked(root / "Tools" / name, tag, owner=root / "Tools")
    require(set(packet["artifact_sha256"]) == set(ARTIFACTS), "the frozen edit artifact inventory differs")
    for name, tag in packet["artifact_sha256"].items():
        baseline.checked(root / name, tag, owner=root)
    prior = admitted_evidence(root, packet["artifact_sha256"]["PriorNativeOpen.json"])
    generated, control = packet["generated"], packet["control"]
    require(packet["oracle_sha256"] == prior["oracle_sha256"] and packet["oracle_file_version"] == prior["oracle_file_version"] == baseline.ORACLE_VERSION
            and generated["writer_revision"] == prior["writer_revision"], "generated candidate identities differ from the prior observation")
    for entry in (generated, control):
        baseline.validate_case(entry["case"])
    require((generated["case"]["name"], generated["case"]["child"]) == (baseline.CANDIDATE, baseline.CANDIDATE_CHILD)
            and (control["case"]["name"], control["case"]["child"]) == (baseline.CONTROL, baseline.CONTROL_CHILD)
            and control["files"] == prior["a18_control_files"] and control["relative_directory"] == baseline.CONTROL_DIRECTORY.as_posix(),
            "the matched edit trial pair identities differ")
    expected = {name: None for name in baseline.DIMENSIONS[:2]} | {baseline.DIMENSIONS[2]: prior["child_authored_scope"]["boss_forward_distance"]["metres"]}
    require(generated["child_parameters_m"] == expected and generated["case"]["dimensions_m"][baseline.DIMENSIONS[2]] == expected[baseline.DIMENSIONS[2]],
            "vertex-authored child parameter contract differs")
    target = generated["case"]["planned_distance_edit_m"]
    require(baseline.close(target - baseline.distance(generated["case"]), DIMENSION_DELTA, relative=0, absolute=1e-14), "the guarded edit increment differs")
    controls = (root.parent / baseline.CONTROL_DIRECTORY).resolve(strict=True)
    frozen = (root / "FrozenGenerated").resolve(strict=True)
    require(controls == root.parent / baseline.CONTROL_DIRECTORY and frozen == root / "FrozenGenerated", "the staged source directory escaped custody")
    baseline.checked(controls.parent / "fresh-reopen/Record.json", control["native_reopen_sha256"], owner=controls.parent)
    sources = baseline.pair_paths(frozen, generated["case"], generated["files"])
    paths = generated["encoded_paths_by_file"]
    require(set(paths) == {source.name for source in sources}
            and all(PureWindowsPath(paths[source.name]) == ENCODED_PARENT / source.name for source in sources), "edit targets differ from the newly encoded directory")
    return packet, baseline.pair_paths(controls, control["case"], control["files"]), sources


def own_paths(entry, sources):
    require(sys.platform == "win32", "native edit stage requires Windows")
    directory = Path(ENCODED_PARENT)
    require(directory.parent.resolve(strict=True) == directory.parent and directory.parent.is_dir() and not directory.parent.is_junction()
            and not os.path.lexists(directory), "the newly encoded edit directory is already occupied or redirected")
    return directory, tuple(Path(entry["encoded_paths_by_file"][source.name]) for source in sources)


def edited_entry(entry):
    case = entry["case"]
    return entry | {"case": case | {"mates": [case["mates"][0] | {"distance_m": case["planned_distance_edit_m"]}]}}


def scene(author, parent, assembly, child_path, entry, phase, snapshot, result):
    baseline.observe(author, parent, assembly, child_path, entry, phase, snapshot, result)
    expected = entry["child_parameters_m"]
    found = result["child_dimensions_m"]
    match = found.keys() == expected.keys() and all(
        (found[name] is None) if value is None else baseline.close(found[name], value, relative=0, absolute=1e-12)
        for name, value in expected.items()
    )
    result["reference_observer_checks"] = result.pop("checks")
    result["reference_observer_matches"] = result.pop("matches")
    result["checks"] = result["reference_observer_checks"] | {"child_dimensions": match}
    result["expected_child_parameters_m"] = expected
    result["matches"] = all(result["checks"].values())


def measure_scene(author, parent, assembly, child, entry, phase, row, label):
    capture = row[label] = {"matches": False}
    author.rec.call(f"measure {label} assembly and child scope", scene, author, parent, assembly, child, entry, phase, row["first_pose"], capture)
    return capture


def drive_d1(author, parent, entry, row):
    import Swapp
    from AssemblyMateEvidence import mate_features

    features = list(islice(mate_features(author, parent), 2))
    require(len(features) == 1, "exactly one assembly distance mate must own D1")
    feature, = features
    require(author.get(feature, "Name") == baseline.MATE and author.get(feature, "GetTypeName2") == "MateDistanceDim",
            "the edit feature does not identify the measured distance mate")
    display = author.get(feature, "GetFirstDisplayDimension")
    require(display is not None, "the measured mate does not expose its display")
    dimension = author.get(display, "GetDimension2", 0)
    require(dimension is not None, "the measured mate does not expose a value dimension")
    name = str(author.get(dimension, "FullName"))
    before = float(author.get(dimension, "SystemValue"))
    target = entry["case"]["planned_distance_edit_m"]
    row.update(full_name=name, before_m=before, target_m=target)
    require(name == f"D1@{baseline.MATE}@{entry['case']['name']}.Assembly"
            and baseline.close(before, baseline.distance(entry["case"]), relative=0, absolute=1e-12),
            "the exact measured D1 must start at its authored value")
    row["setter_status"] = int(author.get(dimension, "SetSystemValue3", target, CURRENT_CONFIGURATION, Swapp.nothing()))
    require(row["setter_status"] == SET_VALUE_SUCCESS, "the native driving dimension setter rejected the edit")
    row["force_rebuild_passed"] = bool(author.get(parent, "ForceRebuild3", False))
    require(row["force_rebuild_passed"], "the edited assembly failed to rebuild")


def save_bundle(author, parent, assembly, paths, entry, result):
    scene = {}
    child = baseline.scene_occurrences(author, assembly, paths[1], entry["case"], baseline.pose_matrices(entry["case"], True), scene)
    require(scene["occurrences_match"], "the owned edited pair changed before save")
    original = {path.name: digest(path) for path in paths}
    child_save, parent_save = {}, {}
    result.update(child=child_save, parent=parent_save)
    require(save_owned(author, child, paths[1], child_save), "owned child save returned errors or warnings")
    require(child_save["before_stamp"] == child_save["after_stamp"], "owned child stamp advanced during save")
    require(save_owned(author, parent, paths[0], parent_save), "owned parent save returned errors or warnings")
    result["files"] = {path.name: {"sha256": digest(path), "bytes": path.stat().st_size} for path in paths}
    result["child_unchanged_by_parent_save"] = result["files"][paths[1].name]["sha256"] == child_save["after_sha256"] and (
        int(author.get(child, "GetUpdateStamp")) == child_save["after_stamp"]
    )
    result["passed"] = result["child_unchanged_by_parent_save"] and all(result["files"][name]["sha256"] != previous for name, previous in original.items())
    require(result["passed"], "owned save did not produce two synchronized new hashes")


def measure(packet, paths, output, row, *, saved=None):
    import Swapp
    from AuthorCurves import CurveAuthor
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity

    source = packet["generated"]
    reopening = saved is not None
    entry = edited_entry(source) if reopening else source
    incoming = saved["files"] if reopening else source["files"]
    baseline.pair_paths(paths[0].parent, entry["case"], incoming)
    recorder = Recorder(output / (row["label"] + "Calls.json"), {"lane": row["label"], "read_only": reopening})
    controller = parent = None
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("verify idle oracle", Swapp.sweep)
            controller = recorder.call("launch fresh owned oracle", Swapp.Sw)
            identity = row["oracle_identity"] = recorder.call("verify pinned executable", application_identity, controller.app)
            require(identity["version_matches"] and identity["file_version"] == baseline.ORACLE_VERSION and identity["sha256"] == packet["oracle_sha256"]
                    and identity["process_id"] == controller.process_id and controller.revision == "34.5.2", "oracle build or ownership differs")
            author = CurveAuthor(controller.app, recorder, Swapp)
            parent, errors, warnings = recorder.call("open exact owned assembly", controller.open, paths[0], read_only=reopening)
            row.update(opened=parent is not None, open_errors=errors, open_warnings=warnings)
            require(parent is not None and errors == warnings == 0 and baseline.exact_file(author.get(parent, "GetPathName"), paths[0]),
                    "owned generated assembly failed its exact open")
            require(bool(author.get(parent, "IsOpenedReadOnly")) == reopening, "native document access state differs from the requested phase")
            assembly = author.typed(parent, "AssemblyDoc")
            row["first_pose"] = baseline.first_pose(author, assembly, entry["case"])
            initial = measure_scene(author, parent, assembly, paths[1], entry, "initial", row, "initial")
            row["forced_rebuild"] = bool(author.get(parent, "ForceRebuild3", False))
            rebuilt = measure_scene(author, parent, assembly, paths[1], entry, "rebuilt", row, "rebuilt")
            require(row["forced_rebuild"] and initial["matches"] and rebuilt["matches"], "authored model did not qualify before the requested phase")
            if reopening:
                require(row["first_pose"]["pose"] == "solved" and initial["child_stamp"] == saved["child"]["after_stamp"],
                        "fresh reopen did not retain the edited placement or saved child identity")
            else:
                drive_d1(author, parent, entry, row.setdefault("edit", {}))
                edited = edited_entry(entry)
                after = measure_scene(author, parent, assembly, paths[1], edited, "rebuilt", row, "edited")
                require(after["matches"], "editing the native D1 did not produce the predicted assembly")
                save_bundle(author, parent, assembly, paths, edited, row.setdefault("save", {}))
            row["passed"] = True
        except Exception as error:
            recorder.failure(error)
            row["exception"] = repr(error)
        finally:
            if controller is not None:
                try:
                    if parent is not None:
                        recorder.call("close owned document", controller.close_doc, parent)
                finally:
                    try:
                        recorder.call("exit owned oracle", controller.close)
                    finally:
                        row["controller_diagnostics"] = controller.diagnostics
    expected = incoming if reopening else row.get("save", {}).get("files", {})
    row["final_input_hashes_match"] = bool(expected and all(digest(path) == expected[path.name]["sha256"] for path in paths))
    row.update(dialogs=monitor.log, progress_windows=monitor.progress)
    row["passed"] = bool(row["passed"] and row["final_input_hashes_match"] and not row["dialogs"] and not row.get("controller_diagnostics")
                         and recorder.data["first_failure"] is None and not recorder.data["cleanup_errors"])
    recorder.data.update(result=row, passed=row["passed"], finished_at=time.time())
    recorder.flush()


def retain_saved(root, paths, expected):
    output = root / "SavedBundle"
    output.mkdir()
    for source in paths:
        target = output / source.name
        with source.open("rb") as reader, target.open("xb") as writer:
            copyfileobj(reader, writer)
        baseline.checked(target, expected[target.name]["sha256"], owner=output, size=expected[target.name]["bytes"])


def run(path, sha):
    packet, control, sources = verify(path, sha)
    root = path.parent
    output = root / "Inspection"
    require(all(not os.path.lexists(location) for location in (output, root / "SavedBundle")), "edit outputs are already occupied")
    output.mkdir()
    record = output / "DistanceMateEditResults.json"
    result = {
        "schema": SCHEMA, "packet_sha256": sha, "writer_revision": packet["generated"]["writer_revision"], "oracle_sha256": packet["oracle_sha256"],
        "heldout_inputs_tested": 0, "heldout_acceptance": False, "native_acceptance": False, "driving_edit_passed": False,
        "native_persistence_passed": False, "controls_healthy": False, "distinct_processes": 0, "passed": False,
        "phases": [], "started_at": time.time(),
    }
    try:
        directory, paths = own_paths(packet["generated"], sources)
    except Exception as error:
        result.update(preflight_exception=repr(error), finished_at=time.time())
        write_json(record, result)
        return result

    def phase(label, *, saved=None):
        row = {"label": label, "passed": False}
        result["phases"].append(row)
        write_json(record, result)
        if label.startswith("Control"):
            baseline.measure(packet, packet["control"], control, output, row)
        else:
            measure(packet, paths, output, row, saved=saved)
        write_json(record, result)
        return row

    edit, reopen = {}, {}
    try:
        if phase("ControlBefore")["passed"]:
            directory.mkdir()
            encoded.stage({"generated_files": packet["generated"]["files"]}, sources, paths, result)
            edit = phase("GeneratedEdit")
            if edit["passed"]:
                reopen = phase("GeneratedReopen", saved=edit["save"])
                if reopen["passed"]:
                    retain_saved(root, paths, edit["save"]["files"])
    except Exception as error:
        result["exception"] = repr(error)
    finally:
        try:
            phase("ControlAfter")
        except Exception as error:
            result["control_after_exception"] = repr(error)
        result["controls_healthy"] = [row["passed"] for row in result["phases"] if row["label"].startswith("Control")] == [True, True]
        try:
            verify(path, sha)
            result["frozen_inputs_unchanged"] = True
        except Exception as error:
            result["frozen_inputs_unchanged"] = False
            result["final_verification_error"] = repr(error)
        identities = {row.get("oracle_identity", {}).get("process_creation_filetime") for row in result["phases"]}
        result["distinct_processes"] = sum(type(value) is int and value > 0 for value in identities)
        result["driving_edit_passed"] = bool(edit.get("edit", {}).get("setter_status") == SET_VALUE_SUCCESS
                                             and edit.get("edit", {}).get("force_rebuild_passed") and edit.get("edited", {}).get("matches"))
        result["native_save_passed"] = bool(edit.get("save", {}).get("passed"))
        result["native_persistence_passed"] = bool(reopen.get("passed"))
        result["passed"] = bool(result["controls_healthy"] and result["frozen_inputs_unchanged"] and result["distinct_processes"] == 4
                                and result["driving_edit_passed"] and result["native_persistence_passed"] and "exception" not in result)
        result["finished_at"] = time.time()
        write_json(record, result)
    return result


def main():
    parser = argparse.ArgumentParser(description="Verify or run the scoped native driving distance edit and save/reopen trial")
    parser.add_argument("mode", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    path = args.packet.resolve(strict=True)
    if args.mode == "verify":
        verify(path, args.packet_sha256)
        print(json.dumps({"verified_edit_packet": args.packet_sha256}))
        return 0
    result = run(path, args.packet_sha256)
    print(json.dumps({key: result[key] for key in ("passed", "driving_edit_passed", "native_persistence_passed", "controls_healthy", "distinct_processes")}))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
