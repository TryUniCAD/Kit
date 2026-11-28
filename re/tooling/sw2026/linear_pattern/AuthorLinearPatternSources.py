from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import Swapp
from AuthorCurves import Recorder, digest, require, write_json
from InspectFresh import healthy, inspect
from LinearPatternAuthor import LinearPatternAuthor
from LinearPatternSpecs import heldout_cases, validate_disclosed
from OracleIdentity import application_identity


ORACLE_HASH = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
SOURCE_SCHEMA = "kit.sw2026.linear-pattern-source-job.v1"
PHASES = ("author", "pristine-reopen", "spacing-edit", "spacing-reopen", "instances-edit", "instances-reopen")


def under(path, parent):
    return path.resolve().is_relative_to(parent.resolve())


def packet_identity(packet):
    manifest_path = packet / "Packet.json"
    manifest = json.loads(manifest_path.read_bytes())
    require(manifest["schema"] == "kit.sw2026.linear-pattern-source-packet.v1", "unexpected source packet")
    require(manifest["source_writer_implemented"] is False and manifest["writer_output_count"] == 0, "source packet cannot contain a pattern writer")
    seen = set()
    for row in manifest["files"]:
        relative = row["path"]
        path = (packet / relative).resolve()
        require(relative not in seen and under(path, packet), "packet contains duplicate or escaping file path")
        seen.add(relative)
        require(path.is_file() and path.stat().st_size == row["bytes"] and digest(path) == row["sha256"], f"frozen source packet differs: {relative}")
    required = {"Tools/AuthorLinearPatternSources.py", "Tools/LinearPatternAuthor.py", "Tools/LinearPatternSpecs.py", "DisclosedInputs02.json", "Control.SLDPRT"}
    require(required <= seen, "source packet is incomplete")
    actual = {str(path.relative_to(packet)).replace("\\", "/") for path in packet.rglob("*") if path.is_file()}
    require(actual == seen | {"Packet.json"}, "frozen packet contains an unbound file or import source")
    return manifest, digest(manifest_path)


def libraries(packet):
    result = json.loads((packet / "Metadata/Result.json").read_bytes())
    require(result["passed"] is True and result["native_processes_started"] == 0 and result["hidden_inputs_read"] == 0, "installed metadata evidence is incomplete")
    reports = {}
    for name, row in result["reports"].items():
        path = packet / "Metadata" / row["path"]
        require(digest(path) == row["sha256"] and path.stat().st_size == row["bytes"], "installed API report changed")
        reports[name] = json.loads(path.read_bytes())
    identities = []
    for name in ("FeatureData", "FeatureId"):
        report = reports[name]
        path = Path(report["path"])
        require(path.is_absolute() and path.is_file() and digest(path) == report["sha256"], "installed typelib bytes differ from the frozen installed metadata")
        identity = report["library_identity"]
        require(identity["major_version"] == 34 and identity["minor_version"] == 0, "wrong installed API version")
        registered = Swapp.pythoncom.LoadRegTypeLib(identity["guid"], 34, 0, 0)
        attributes = registered.GetLibAttr()
        require(str(attributes[0]).casefold() == identity["guid"].casefold() and list(attributes[1:5]) == [identity["locale_id"], identity["system_kind"], 34, 0], "registered loaded library identity differs from the pinned metadata")
        identities.append({"name": path.name, "sha256": report["sha256"], "library_identity": identity, "registered_library_identity_matches": True})
    return identities


def settings(case, phase):
    spacing = case["edit_spacing_m"] if phase in ("spacing-edit", "spacing-reopen") else case["spacing_m"]
    instances = case["edit_instances"] if phase in ("instances-edit", "instances-reopen") else case["instances"]
    return spacing, instances


def run_phase(case, phase, directory, inputs, expected_hash):
    record_path = directory / phase / "Record.json"
    record_path.parent.mkdir(parents=True, exist_ok=False)
    recorder = Recorder(record_path, {"case": case, "phase": phase})
    recorder.data["schema"] = "kit.sw2026.linear-pattern-source-phase.v1"
    recorder.data.update(source_writer_implemented=False, writer_output_count=0)
    pristine, derivative = inputs
    source = pristine if phase in ("pristine-reopen", "spacing-edit", "instances-edit") else derivative
    target = pristine if phase == "author" else derivative
    source_hash = None if phase == "author" else expected_hash
    complete, session = False, None
    try:
        require(phase in PHASES, "unexpected source phase")
        if phase == "author" or phase.endswith("-edit"):
            require(not target.exists(), "fresh native source target already exists")
        if phase != "author":
            require(source.is_file() and digest(source) == source_hash, "immutable source changed before opening")
    except Exception as error:
        recorder.failure(error)
        recorder.data["passed"] = False
        recorder.flush()
        return recorder.data, digest(record_path)
    with Swapp.Dismisser() as monitor:
        try:
            session = recorder.call("launch isolated .34 COM", Swapp.Sw)
            identity = recorder.call("oracle identity", application_identity, session.app)
            recorder.data["oracle_identity"] = identity
            recorder.flush()
            require(identity["version_matches"] and identity["sha256"] == ORACLE_HASH and identity["pe_machine"] == "0x8664" and session.revision == "34.5.2", "incorrect native executable")
            author = LinearPatternAuthor(session.app, recorder, Swapp)
            if phase == "author":
                author.build(case, session)
                author.snapshot(case, "authored", case["spacing_m"], case["instances"])
            else:
                author.model, errors, warnings = recorder.call("open immutable native source", session.open, source, read_only=not phase.endswith("-edit"))
                recorder.data["open"] = {"opened": author.model is not None, "errors": errors, "warnings": warnings}
                recorder.flush()
                require(author.model is not None and errors == warnings == 0, "native source open failed or warned")
                if phase.endswith("-edit"):
                    author.snapshot(case, "before_edit", case["spacing_m"], case["instances"])
                    author.edit(case, "spacing" if phase == "spacing-edit" else "instances")
                author.snapshot(case, "edited" if phase.endswith("-edit") else "reopened", *settings(case, phase))
            if phase == "author" or phase.endswith("-edit"):
                result = recorder.call("save new native source", session.save_as, author.model, target)
                recorder.data["save"] = {"target": str(target), "ok": result[0], "errors": result[1], "warnings": result[2]}
                recorder.flush()
                require(result == (True, 0, 0) and target.is_file() and target.stat().st_size > 0, "native source save failed or warned")
                saved_path = str(author.get(author.model, "GetPathName"))
                require(Path(saved_path) == target, "native save did not retain the requested actual document path")
                recorder.data["exports"] = []
                for suffix in (".x_t", ".step"):
                    exported = target.with_suffix(suffix)
                    require(not exported.exists(), "fresh independent geometry export target already exists")
                    exported_result = recorder.call("export independent geometry sibling", session.save_as, author.model, exported)
                    require(exported_result == (True, 0, 0) and exported.is_file() and exported.stat().st_size > 0, "native geometry sibling export failed or warned")
                    require(str(author.get(author.model, "GetPathName")) == saved_path, "geometry export changed the actual native source document identity")
                    recorder.data["exports"].append({"name": exported.name, "sha256": digest(exported), "bytes": exported.stat().st_size})
                    recorder.flush()
            complete = True
        except Exception as error:
            recorder.failure(error)
        finally:
            if session is not None:
                try:
                    session.close()
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                recorder.data["controller_diagnostics"] = session.diagnostics
    recorder.data["dialogs"] = monitor.log
    recorder.data["source_immutable"] = phase == "author" or bool(source.is_file() and digest(source) == source_hash)
    artifact = target if phase == "author" or phase.endswith("-edit") else source
    if artifact.is_file():
        recorder.data.update(native_sha256=digest(artifact), native_bytes=artifact.stat().st_size)
    recorder.data["passed"] = bool(complete and recorder.data["source_immutable"] and recorder.data.get("native_sha256") and not recorder.data["first_failure"] and not recorder.data["dialogs"] and not recorder.data.get("controller_diagnostics"))
    recorder.data["finished_at"] = time.time()
    recorder.flush()
    return recorder.data, digest(record_path)


def run_case(case, output):
    directory = output / case["name"]
    directory.mkdir(parents=True, exist_ok=False)
    pristine = directory / (case["name"] + ".SLDPRT")
    spacing = directory / (case["name"] + "Spacing.SLDPRT")
    instances = directory / (case["name"] + "Instances.SLDPRT")
    phases, artifacts, identities = [], {}, []
    pristine_hash = None
    for phase in PHASES:
        derivative = spacing if phase.startswith("spacing-") else instances
        source_hash = artifacts.get("spacing-edit" if phase == "spacing-reopen" else "instances-edit") if phase in ("spacing-reopen", "instances-reopen") else pristine_hash
        record, receipt = run_phase(case, phase, directory, (pristine, derivative), source_hash)
        phases.append({"phase": phase, "record_sha256": receipt, "passed": bool(record.get("passed")), "native_sha256": record.get("native_sha256"), "native_bytes": record.get("native_bytes"), "exports": record.get("exports", [])})
        if "oracle_identity" in record:
            identities.append(record["oracle_identity"]["process_creation_filetime"])
        if not record.get("passed"):
            break
        artifacts[phase] = record["native_sha256"]
        if phase == "author":
            pristine_hash = record["native_sha256"]
        require(digest(pristine) == pristine_hash, "pristine native source changed during an independent edit branch")
    return {"name": case["name"], "split": case["split"], "phases": phases, "native_sources": [{"name": path.name, "sha256": digest(path), "bytes": path.stat().st_size} for path in (pristine, spacing, instances) if path.is_file()], "passed": len(phases) == 6 and all(row["passed"] for row in phases)}, identities


def control_phase(control, expected_hash, path):
    record = {}
    try:
        require(digest(control) == expected_hash, "frozen control changed before inspection")
        inspect(control, result=record, checkpoint=lambda: write_json(path, record))
    except Exception as error:
        record["exception"] = repr(error)
    write_json(path, record)
    passed = bool(healthy(record) and record.get("sha256") == expected_hash and record.get("oracle_identity", {}).get("sha256") == ORACLE_HASH and digest(control) == expected_hash)
    return {"passed": passed, "record_sha256": digest(path)}, record.get("oracle_identity", {}).get("process_creation_filetime")


def load_job(path, packet, packet_hash):
    job = json.loads(path.read_bytes())
    require(job["schema"] == SOURCE_SCHEMA and job["packet_sha256"] == packet_hash, "job does not bind the exact packet")
    require(re.fullmatch(r"[0-9a-f]{40}", job["source_revision"]), "job must bind a published exact source revision")
    require(job["cohort"] in ("disclosed", "heldout"), "source cohort is not explicit")
    checkout = Path(job["checkout_root"])
    output, public_lock = Path(job["output"]), Path(job["public_lock"])
    require(all(item.is_absolute() for item in (checkout, output, public_lock)), "absolute source paths are required")
    require(not under(output, checkout) and not under(public_lock, checkout), "oracle source output must stay outside the checkout")
    require(not output.exists() and not public_lock.exists(), "source output or lock already exists")
    require(not under(output, packet) and not under(packet, output) and not under(public_lock, packet) and not under(path, packet), "immutable packet, bound job and mutable source output must be disjoint")
    if job["cohort"] == "heldout":
        require(output.drive.upper() == output.resolve().drive.upper() == "C:" and Path("C:/KitLinearPatternSealed").resolve().drive.upper() == "C:" and not str(output).startswith("\\\\") and under(output, Path("C:/KitLinearPatternSealed")), "held-out raw inputs and observations must remain in the fixed guest-private C: root")
        require(not under(public_lock, output), "public sealed lock must not be mistaken for a raw guest-private result")
    return job, output, public_lock


def run(job_path, packet, packet_hash):
    job, output, public_lock = load_job(job_path, packet, packet_hash)
    installed = libraries(packet)
    control = packet / "Control.SLDPRT"
    control_hash = digest(control)
    prior_lock, prior_hash = None, None
    if job["cohort"] == "heldout":
        prior_lock = public_lock.with_name("disclosed-lock.json")
        require(prior_lock.is_file(), "qualified disclosed source batch is required before guest-private authoring")
        prior = json.loads(prior_lock.read_bytes())
        require(prior["schema"] == "kit.sw2026.linear-pattern-source-lock.v1" and prior["passed"] is True and prior["cohort"] == "disclosed" and prior["packet_sha256"] == packet_hash and prior["source_revision"] == job["source_revision"] and prior["writer_output_count"] == 0 and prior["distinct_processes"] == 14, "held-out authoring requires this exact qualified disclosed method")
        prior_hash = digest(prior_lock)
    output.mkdir(parents=True, exist_ok=False)
    public_lock.parent.mkdir(parents=True, exist_ok=True)
    private_specs = output / "FrozenInputs.json"
    specs = {"schema": "kit.sw2026.linear-pattern-disclosed-inputs.v2", "cases": heldout_cases()} if job["cohort"] == "heldout" else json.loads((packet / "DisclosedInputs02.json").read_bytes())
    cases = specs["cases"] if job["cohort"] == "heldout" else validate_disclosed(specs)
    write_json(private_specs, specs)
    evidence = {"schema": "kit.sw2026.linear-pattern-source-lock.v1", "task_id": "B04-SW2026-LOCAL-LINEAR-PATTERN", "source_revision": job["source_revision"], "cohort": job["cohort"], "packet_sha256": packet_hash, "job_sha256": digest(job_path), "specs_sha256": digest(private_specs), "qualified_disclosed_lock_sha256": prior_hash, "control_sha256": control_hash, "oracle_sha256": ORACLE_HASH, "installed_libraries": installed, "started_at": time.time(), "cases": [], "controls": {}, "writer_output_count": 0, "source_writer_implemented": False, "heldout_raw_remains_guest_private": job["cohort"] == "heldout", "native_acceptance": False, "heldout_acceptance": False, "passed": False, "application_pids_before": sorted(Swapp.application_pids())}
    write_json(public_lock, evidence)
    identities = []
    try:
        evidence["controls"]["before"], identity = control_phase(control, control_hash, output / "ControlBefore.json")
        if identity is not None:
            identities.append(identity)
        write_json(public_lock, evidence)
        if evidence["controls"]["before"]["passed"]:
            for case in cases:
                row, phase_identities = run_case(case, output)
                evidence["cases"].append(row)
                identities.extend(phase_identities)
                write_json(public_lock, evidence)
                if not row["passed"]:
                    break
    except Exception as error:
        evidence["batch_exception"] = {"type": type(error).__name__, "private_diagnostic": "PrivateFailure.json"}
        write_json(output / "PrivateFailure.json", {"type": type(error).__name__, "error": repr(error)})
    finally:
        evidence["controls"]["after"], identity = control_phase(control, control_hash, output / "ControlAfter.json")
        if identity is not None:
            identities.append(identity)
        try:
            _, final_packet_hash = packet_identity(packet)
            packet_unchanged = final_packet_hash == packet_hash
        except Exception as error:
            packet_unchanged = False
            evidence["final_packet_verification_error"] = type(error).__name__
        evidence.update(packet_unchanged=packet_unchanged, inputs_unchanged=digest(job_path) == evidence["job_sha256"] and digest(private_specs) == evidence["specs_sha256"] and (prior_lock is None or digest(prior_lock) == prior_hash), control_unchanged=digest(control) == control_hash, completed_native_phases=len(identities), distinct_processes=len(set(identities)), expected_native_phases=14, application_pids_after=sorted(Swapp.application_pids()), finished_at=time.time())
        evidence["passed"] = bool(all(row["passed"] for row in evidence["controls"].values()) and set(evidence["controls"]) == {"before", "after"} and len(evidence["cases"]) == 2 and all(row["passed"] for row in evidence["cases"]) and evidence["packet_unchanged"] and evidence["inputs_unchanged"] and evidence["control_unchanged"] and not evidence["application_pids_before"] and not evidence["application_pids_after"] and len(identities) == len(set(identities)) == 14 and "batch_exception" not in evidence)
        write_json(output / "SourceLock.json", evidence)
        write_json(public_lock, evidence)
    Swapp.emit({"passed": evidence["passed"], "source_cases": len(evidence["cases"]), "distinct_native_processes": len(set(identities)), "writer_output_count": 0, "public_lock_sha256": digest(public_lock)})
    return int(not evidence["passed"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", type=Path)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    require(args.verify_only != (args.job is not None), "choose only packet verification or a bound source job")
    packet = Path(__file__).resolve().parent.parent
    manifest, packet_hash = packet_identity(packet)
    if args.verify_only:
        Swapp.emit({"packet_sha256": packet_hash, "files": len(manifest["files"]), "installed_libraries": libraries(packet), "native_processes_started": 0, "passed": True})
        return 0
    return run(args.job.resolve(), packet, packet_hash)


if __name__ == "__main__":
    raise SystemExit(main())
