from functools import partial
import json
from pathlib import Path
from time import time

from ThinHeldoutPacket import (
    CASES, DISCLOSURE_SHA, LOCK_SHA, ORACLE, ORIGINALS, SCHEMA, SPEC, VERSION,
    checked, digest, encode, packet_data, publish, require,
)


def indexed_sources(cases, lock, generation, work):
    source_root = Path(ORIGINALS)
    require(source_root.is_dir() and not source_root.is_symlink(), "locked local native root differs")
    for slot, case, row in zip(CASES, cases, lock["sources"], strict=True):
        require(row["case"] == slot, "locked native slot order differs")
        name = case["name"]
        directory = source_root / name
        require(directory.is_dir() and not directory.is_symlink(), "missing native source folder")
        original = directory / (name + ".SLDPRT")
        require(len(checked(original, row["native_sha256"])) == row["native_bytes"], "locked native source size differs")
        prior = {}
        for evidence, filename in zip(row["phases"], (name + ".author.json", name + ".reopen.json",
                                                  name + "-edited.edited-reopen.json"), strict=True):
            path = directory / filename
            prior[evidence["phase"]] = (path, evidence["sha256"])
            checked(path, evidence["sha256"])
        proof = generation["cases"][slot]
        require(proof["typed_streams"] == 10 and proof["repeat_bytes_equal"]
                and proof["writer_runtime_external_access_attempts"] == 0, "candidate proof lost its writer guard")
        candidate = work / "Generated" / (name + ".SLDPRT")
        require(len(checked(candidate, proof["candidate_sha256"])) == proof["candidate_bytes"],
                "frozen candidate size differs")
        yield slot, case, original, row["native_sha256"], candidate, proof, prior


def public_phase(phase):
    fields = ("phase", "sha256", "passed", "open_status", "cold_bodies", "checks", "checks_passed")
    return {key: phase[key] for key in fields}


def public_comparison(comparison):
    return {phase: {key: row[key] for key in ("tree_rows", "driver_count", "numeric_geometry_checks")}
            for phase, row in comparison.items()}


def compare_slot(inputs, output, runner):
    from CompareThinNative import compare_cycle
    from RunThinNative import check_phase

    slot, case, original, source_sha, candidate, proof, prior = inputs
    root = output / slot
    copy = root / "PrivateSource" / original.name
    copy.parent.mkdir(parents=True)
    publish(copy, checked(original, source_sha))
    row = {"slot": slot, "source_sha256": source_sha, **proof, "passed": False}
    stage = "native_phases"
    try:
        source, source_phases = runner(case, copy, source_sha, root / "Source")
        generated, candidate_phases = runner(case, candidate, proof["candidate_sha256"], root / "Candidate")
        row["native_phases"] = {"source": list(map(public_phase, source_phases)),
                                "candidate": list(map(public_phase, candidate_phases))}
        stage = "cold_edit_and_reopen"
        roles = ("angle", "wall1", "wall2") if case["wall_mode"] == "two" else ("angle", "wall1")
        for phases in (source, generated):
            require(len(phases) == 2, "native edit, save and fresh reopen chain was incomplete")
            check_phase(phases[0], roles)
            check_phase(phases[1])
        stage = "same_mode_source_baseline"
        recorded = tuple(json.loads(checked(*prior[label])) for label in ("author", "reopen", "edited-reopen"))
        require(recorded[0]["native_sha256"] == source_sha and all(r["passed"] for r in recorded),
                "the locked native author phase differs")
        recorded_phases = recorded[1:]
        source_reference = compare_cycle(source, recorded_phases, case["wall_mode"])
        stage = "candidate_source_parity"
        candidate_reference = compare_cycle(generated, source, case["wall_mode"])
        row["comparisons"] = {"source_to_pre_writer": public_comparison(source_reference),
                              "candidate_to_current_source": public_comparison(candidate_reference)}
        row["cold_root_feature_counts"] = {label: [len(phase["before_explicit_rebuild"]["features"]) for phase in phases]
                                           for label, phases in (("source", source), ("candidate", generated))}
        row["edited_driver_roles"] = list(roles)
        row["passed"] = True
    except Exception as error:
        publish(root / "PrivateFailure.json", encode({"stage": stage, "error": repr(error)}))
        row.update(failure_stage=stage, error_type=type(error).__name__)
    return row


def run_native(packet, pin, generation_pin, manifest, lock, work, cases, generation):
    import Swapp
    from AuthorCurves import write_json
    from AuthorRevolveFamilies import author_type, constants_from_registration
    from AuthorRevolveSources import PLANES, RevolveAuthor, run_phase
    from InspectFresh import healthy, inspect
    from RunThinNative import run_lane

    def idle():
        return not Swapp.application_pids() and not Swapp.owned_process_ids()

    require(idle(), "SOLIDWORKS application or owned controller remains active")
    inputs = tuple(indexed_sources(cases, lock, generation, work))
    target = work / "PrivateOracle"
    target.mkdir()
    control = packet / "Control.SLDPRT"
    control_sha = lock["control_sha256"]
    local_control = target / "Control.SLDPRT"
    publish(local_control, checked(control, control_sha))
    constants = constants_from_registration(Swapp)
    require(constants == lock["registered_swconst"], "registered native values differ from the independent source lock")
    author = author_type(RevolveAuthor, PLANES, Swapp, constants)
    processes = []
    report = {"schema": SCHEMA, "freeze_sha256": pin, "generation_sha256": generation_pin,
              "source_lock_sha256": LOCK_SHA, "disclosed_sha256": DISCLOSURE_SHA,
              "principal_disclosed_sha256": manifest.get("principal_native_sha256"),
              "profile": manifest.get("profile", "front"),
              "writer_revision": manifest["writer"], "writer_src_tree": manifest["writer_src_tree"],
              "oracle_build": VERSION, "oracle_sha256": ORACLE, "started_at": time(),
              "original_native_files_read_during_generation": 0, "writer_runtime_external_access_attempts": 0,
              "public_writer_qualified": False, "whole_source_conversion": False, "cases": []}

    def record_process(row):
        native = row.get("oracle_identity")
        if native is not None:
            require(native["sha256"] == ORACLE and native["file_version"] == VERSION
                    and native["pe_machine"] == "0x8664" and native["version_matches"],
                    "native process does not match the pinned SP05.2 executable")
            processes.append(native["process_creation_filetime"])

    def bracket(label):
        require(idle(), "native application remained active before bracket control")
        checked(local_control, control_sha)
        row = inspect(local_control)
        target_file = target / (label + ".json")
        write_json(target_file, row)
        record_process(row)
        report[label] = {"passed": bool(healthy(row) and row["sha256"] == control_sha
                                        and "oracle_identity" in row),
                         "sha256": digest(target_file.read_bytes())}

    try:
        bracket("control-before")
        if report["control-before"]["passed"]:
            observe = partial(run_lane, author=author, run_phase=run_phase, record_process=record_process, idle=idle)
            for row in inputs:
                report["cases"].append(compare_slot(row, target, observe))
    except Exception as error:
        publish(target / "PrivateBatchFailure.json", encode({"error": repr(error)}))
        report["batch_failure_type"] = type(error).__name__
    finally:
        try:
            bracket("control-after")
        except Exception as error:
            publish(target / "PrivateControlFailure.json", encode({"error": repr(error)}))
            report["control-after"] = {"passed": False, "error_type": type(error).__name__}
    try:
        checked(local_control, control_sha)
        checked(Path(SPEC), lock["spec_sha256"])
        manifest, _, _ = packet_data(packet, pin)
        checked(packet / "Code.zip", manifest["code_sha256"])
        checked(work / "Generation.json", generation_pin)
        tuple(indexed_sources(cases, lock, generation, work))
        custody = True
    except (ValueError, OSError):
        custody = False
    report.update(fresh_processes=len(processes), distinct_processes=len(set(processes)), idle_after=idle(),
                  immutable_inputs_reverified=custody, finished_at=time())
    report["passed"] = bool(not report.get("batch_failure_type") and report.get("control-before", {}).get("passed")
                            and report["control-after"]["passed"] and report["idle_after"] and custody
                            and report["fresh_processes"] == report["distinct_processes"] == 18
                            and len(report["cases"]) == len(CASES) and all(row["passed"] for row in report["cases"]))
    report["heldout_writer_cases_qualified"] = len(CASES) if report["passed"] else 0
    return {"passed": report["passed"], "receipt_sha256": publish(packet / "NativeReceipt.json", encode(report)),
            "heldout_writer_cases_qualified": report["heldout_writer_cases_qualified"]}
