from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path, PureWindowsPath
from shutil import copyfile

from AuthorCurves import digest, require, write_json
from AuthorReferencePlaneSources import PlaneAuthor, metadata
from NestedAssemblySourcePlan import CONTROL_SHA, ORACLE, checked, valid_sha
from ReferencePlaneSourcePlan import SCHEMA as CASE_SCHEMA, SLOT_IDS, disclosed_cases, geometry, heldout_cases, validate_case
from RunSealedNestedSourcePhase import PrivateRecorder, local_trial, opaque_identity, value_hash


SCRIPT = Path(__file__).resolve()
SCHEMA = "kit.sw2026.offset-plane-source-phases.v1"
TOOLS = ("AuthorCurves.py", "AuthorAssemblySources.py", "InspectFresh.py", "InspectCircleSketch.py", "ObserveAssemblyLoad.py", "OracleIdentity.py", "Swapp.py",
         "NestedAssemblySourcePlan.py", "AuthorNestedAssemblySources.py", "RunSealedNestedSourcePhase.py",
         "ReferencePlaneSourcePlan.py", "AuthorReferencePlaneSources.py", SCRIPT.name)
PHASES = ("metadata", "before", "author", "reopen", "after", "lock", "seal")


def prepare(args):
    root = args.output.resolve()
    require(root.parent.is_dir() and not root.exists() and not root.is_relative_to(SCRIPT.parents[3]), "choose an unused private plane source packet")
    seed = checked(args.control, CONTROL_SHA)
    base = PureWindowsPath(args.guest_private_base)
    require(base.is_absolute() and re.fullmatch(r"[A-Za-z]:", base.drive) and ".." not in base.parts, "choose a private fixed-drive guest source directory")
    root.mkdir()
    (root / "Tools").mkdir()
    copyfile(seed, root / "Control.SLDPRT")
    hashes = {}
    for name in TOOLS:
        copyfile(SCRIPT.parent / name, root / "Tools" / name)
        hashes[name] = digest(root / "Tools" / name)
    write_json(root / "Disclosed.json", {"schema": CASE_SCHEMA, "cases": disclosed_cases()})
    file = root / "Source.json"
    write_json(file, {"schema": SCHEMA, "oracle_sha256": ORACLE, "control_sha256": CONTROL_SHA, "tools_sha256": hashes,
                      "disclosed_sha256": digest(root / "Disclosed.json"), "guest_private_base": str(base), "writer_output_count": 0,
                      "heldout_designs_guest_private": True, "native_acceptance": False})
    sha = digest(file)
    subprocess.run([sys.executable, "-B", str(root / "Tools" / SCRIPT.name), "verify", str(file), "--packet-sha256", sha],
                   check=True, capture_output=True, timeout=30)
    return {"packet": str(file), "packet_sha256": sha, "tools_sha256": hashes, "heldout_inputs_read": 0}


def verify(file, sha):
    root = file.parent
    packet = json.loads(checked(file, sha, root).read_bytes())
    require(file.name == "Source.json" and packet["schema"] == SCHEMA and packet["oracle_sha256"] == ORACLE and packet["control_sha256"] == CONTROL_SHA and
            packet["writer_output_count"] == 0 and packet["native_acceptance"] is False and packet["heldout_designs_guest_private"] is True,
            "unexpected plane source packet")
    tools = root / "Tools"
    require(SCRIPT.parent == tools and set(packet["tools_sha256"]) == set(TOOLS), "use the frozen plane source tools")
    for name, wanted in packet["tools_sha256"].items():
        checked(tools / name, wanted, tools)
    checked(root / "Control.SLDPRT", CONTROL_SHA, root)
    cases = json.loads(checked(root / "Disclosed.json", packet["disclosed_sha256"], root).read_bytes())
    require(cases == {"schema": CASE_SCHEMA, "cases": disclosed_cases()}, "disclosed plane source inputs differ")
    return packet


def prior(root, case_id, phase, sha):
    file = root / "Progress" / case_id / phase / "Record.json"
    row = json.loads(file.read_bytes())
    require(row["packet_sha256"] == sha and row["case_id"] == case_id and row["phase"] == phase and row["passed"] is True and row["stage"] == "passed",
            "plane source prerequisite is incomplete")
    return row


def private_root(packet, sha, case_id):
    slot = 0 if case_id == "D00" else int(case_id[1:]) + (100 if case_id.startswith("H") else 0)
    return local_trial(packet, sha, slot, "T01")


def artifact_manifest(saved):
    return {role: {key: row[key] for key in ("bytes", "sha256")} for role, row in saved.items()}


def assert_saved(saved, paths):
    require(set(saved) == set(paths), "source and edited native sibling closure differs")
    for role, path in paths.items():
        row = saved[role]
        require(row["status"] == [True, 0, 0] and checked(path, row["sha256"], path.parent).stat().st_size == row["bytes"], "saved native plane source changed")


def case_inputs(packet_path, packet, sha, case_id):
    if case_id.startswith("D"):
        case, = [row for row in disclosed_cases() if row["id"] == case_id]
        return case
    seal = prior(packet_path.parent, "D00", "seal", sha)
    base = private_root(packet, sha, "D00")
    pack = json.loads(checked(base / "SealedSpecs.json", seal["sealed_spec_sha256"], base).read_bytes())
    require(pack["schema"] == CASE_SCHEMA and len(pack["cases"]) == 2, "sealed plane source pack differs")
    case, = [validate_case(row) for row in pack["cases"] if row["id"] == case_id]
    require(case["split"] == "heldout", "sealed source slot is not held out")
    return case


def measure_case(phase, case, native, raw, prior_path, publish, expected_api):
    import Swapp
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity

    recorder = PrivateRecorder(raw, {"case": case, "phase": phase}, publish)
    result = {"passed": False}
    controller = None
    paths = {"source": native / (case["name"] + ".SLDPRT"), "edited": native / (case["name"] + "Edited.SLDPRT")}
    api = metadata()
    require(api == expected_api, "registered reference-plane API metadata changed after preflight")
    recorder.data["reference_plane_api"] = api
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("verify idle oracle", Swapp.sweep)
            controller = recorder.call("launch fresh source oracle", Swapp.Sw)
            identity = recorder.call("verify exact source oracle", application_identity, controller.app)
            require(identity["version_matches"] and identity["sha256"] == ORACLE and controller.revision == "34.5.2", "unexpected source oracle build")
            result["oracle_identity"] = identity
            publish(stage="native_source", identity=opaque_identity(identity))
            author = PlaneAuthor(controller.app, recorder, Swapp, api)
            if phase == "author":
                native.mkdir(exist_ok=False)
                author.build(case, controller)
                result["initial"] = author.snapshot(case)
                status = list(recorder.call("save original native source", controller.save_as, author.model, paths["source"]))
                require(status == [True, 0, 0] and paths["source"].is_file(), "native source save failed or warned")
                source_sha = digest(paths["source"])
                result["saved_files"] = {"source": {"status": status, "sha256": source_sha, "bytes": paths["source"].stat().st_size}}
                author.edit_plane(case["edit_distance_m"])
                result["edited"] = author.snapshot(case, True)
                require(result["initial"]["mass_properties"]["com"] != result["edited"]["mass_properties"]["com"], "plane distance edit did not move its supported solid")
                status = list(recorder.call("save independent edited native sibling", controller.save_as, author.model, paths["edited"]))
                require(status == [True, 0, 0] and digest(paths["source"]) == source_sha, "edited save failed or changed the original source")
                result["saved_files"]["edited"] = {"status": status, "sha256": digest(paths["edited"]), "bytes": paths["edited"].stat().st_size}
                result["exports"] = {}
                for kind, suffix in (("parasolid", ".x_t"), ("step", ".step")):
                    target = native / (case["name"] + "Edited" + suffix)
                    status = list(recorder.call("export independent edited geometry sibling", controller.save_as, author.model, target))
                    require(status == [True, 0, 0] and target.is_file() and target.stat().st_size > 0, "native geometry sibling export failed or warned")
                    result["exports"][kind] = {"status": status, "bytes": target.stat().st_size, "sha256": digest(target)}
                    assert_saved(result["saved_files"], paths)
                snapshot = native.parent / "SavedAuthor.json"
                write_json(snapshot, {"case": case, "result": result, "artifact_manifest": artifact_manifest(result["saved_files"])})
                publish(stage="source_files_locked", native_artifact_manifest_sha256=value_hash(artifact_manifest(result["saved_files"])),
                        private_saved_snapshot_sha256=digest(snapshot))
            else:
                authored = json.loads(prior_path.read_bytes())
                require(authored["case"] == case, "saved source case differs")
                result["saved_files"] = authored["result"]["saved_files"]
                assert_saved(result["saved_files"], paths)
                for role, edited in (("source", False), ("edited", True)):
                    model, errors, warnings = recorder.call("fresh-read exact native plane sibling", controller.open, paths[role], read_only=True)
                    require(model is not None and errors == warnings == 0 and Path(author.get(model, "GetPathName")).samefile(paths[role]), "plane source sibling failed or warned on fresh open")
                    author.model = model
                    require(author.get(model, "ForceRebuild3", False), "fresh source sibling rebuild failed")
                    observed = author.snapshot(case, edited)
                    require(observed["feature_tree"] == authored["result"]["edited" if edited else "initial"]["feature_tree"], "native plane source tree changed on reopen")
                    result[role] = {"open_errors": errors, "open_warnings": warnings, "observed": observed}
                    controller.close_doc(model)
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["error"] = repr(error)
        finally:
            if controller is not None:
                publish(stage="closing_oracle")
                controller.close()
                result["controller_diagnostics"] = controller.diagnostics
    result["dialogs"], result["progress_windows"] = monitor.log, monitor.progress
    result["passed"] = bool(result["passed"] and not result["dialogs"] and not result.get("controller_diagnostics") and not recorder.data["cleanup_errors"])
    if result["passed"]:
        assert_saved(result["saved_files"], paths)
    recorder.data.update(result=result, passed=result["passed"], finished_at=time.time())
    recorder.flush()
    require(result["passed"], "native plane source phase failed")
    return {"identity": opaque_identity(result["oracle_identity"]), "native_artifact_manifest_sha256": value_hash(artifact_manifest(result["saved_files"]))}


def control(seed, raw):
    from InspectFresh import healthy, inspect

    result = inspect(seed)
    write_json(raw, result)
    require(digest(seed) == CONTROL_SHA and healthy(result) and result["oracle_identity"]["sha256"] == ORACLE, "plane source bracket failed")
    return {"identity": opaque_identity(result["oracle_identity"])}


def lock_case(root, packet, sha, case_id):
    author = prior(root, case_id, "author", sha)
    reopen = prior(root, case_id, "reopen", sha)
    require(author["native_artifact_manifest_sha256"] == reopen["native_artifact_manifest_sha256"] and author["finished_at"] <= reopen["started_at"] and
            author["identity"]["process_creation_filetime"] != reopen["identity"]["process_creation_filetime"], "native source author and reopen do not qualify")
    if case_id.startswith("H"):
        before, after = [prior(root, case_id, phase, sha) for phase in ("before", "after")]
        rows = [before, author, reopen, after]
        require(len({row["identity"]["process_creation_filetime"] for row in rows}) == 4 and
                all(first["finished_at"] <= second["started_at"] for first, second in zip(rows, rows[1:])), "sealed plane source brackets do not qualify")
    case = case_inputs(root / "Source.json", packet, sha, case_id)
    case_root = private_root(packet, sha, case_id) if case_id.startswith("H") else root / "Disclosed" / case_id
    saved = json.loads(checked(case_root / "SavedAuthor.json", author["private_saved_snapshot_sha256"], case_root).read_bytes())
    require(saved["case"] == case, "source lock snapshot differs from its declared case")
    paths = {"source": case_root / "Native" / (case["name"] + ".SLDPRT"), "edited": case_root / "Native" / (case["name"] + "Edited.SLDPRT")}
    assert_saved(saved["result"]["saved_files"], paths)
    require(value_hash(artifact_manifest(saved["result"]["saved_files"])) == author["native_artifact_manifest_sha256"], "native plane source manifest changed before lock")
    return {"heldout_source_locked": case_id.startswith("H"), "source_locked": True,
            "native_artifact_manifest_sha256": author["native_artifact_manifest_sha256"], "private_saved_snapshot_sha256": author["private_saved_snapshot_sha256"]}


def seal(root, packet, sha):
    prior(root, "D00", "metadata", sha)
    before, after = [prior(root, "D00", phase, sha) for phase in ("before", "after")]
    rows = [before]
    for case in disclosed_cases():
        rows.extend(prior(root, case["id"], phase, sha) for phase in ("author", "reopen"))
        lock_case(root, packet, sha, case["id"])
    rows.append(after)
    require(len({row["identity"]["process_creation_filetime"] for row in rows}) == 10 and
            all(first["finished_at"] <= second["started_at"] for first, second in zip(rows, rows[1:])), "disclosed source cohort lacks healthy ordered native brackets")
    private = private_root(packet, sha, "D00")
    file = private / "SealedSpecs.json"
    require(not file.exists(), "sealed source designs are immutable")
    write_json(file, {"schema": CASE_SCHEMA, "cases": heldout_cases(), "created_at": time.time()})
    return {"sealed_spec_sha256": digest(file), "sealed_source_designs_created": True}


def run(args, file, packet):
    require(os.name == "nt", "plane source phases run only in the Windows guest")
    case_id, phase = args.case_id, args.phase
    require((case_id == "D00" and phase in ("metadata", "before", "after", "seal")) or (case_id in SLOT_IDS and phase in ("author", "reopen", "lock")) or
            (case_id.startswith("H") and phase in ("before", "after")), "phase is outside its source slot")
    root = file.parent
    output = root / "Progress" / case_id / phase
    output.mkdir(parents=True, exist_ok=False)
    state = {"schema": SCHEMA, "packet_sha256": args.packet_sha256, "case_id": case_id, "phase": phase, "stage": "verifying", "passed": False,
             "started_at": time.time(), "writer_output_count": 0}
    allowed = {"stage", "progress_at", "identity", "passed", "finished_at", "private_record_sha256", "native_artifact_manifest_sha256", "private_saved_snapshot_sha256",
               "heldout_source_locked", "source_locked", "sealed_spec_sha256", "sealed_source_designs_created", "api_metadata_sha256"}

    def publish(**changes):
        require(set(changes) <= allowed, "private source detail cannot be published")
        state.update(changes)
        write_json(output / "Record.json", state)

    publish()
    raw = None
    try:
        private = private_root(packet, args.packet_sha256, case_id)
        raw_root = private / phase
        raw_root.mkdir(exist_ok=False)
        raw = raw_root / "Private.json"
        with (raw_root / "Console.log").open("w", encoding="utf-8") as stream, redirect_stdout(stream), redirect_stderr(stream):
            if phase == "metadata":
                observed = metadata()
                write_json(raw, observed)
                write_json(root / "ApiMetadata.json", observed)
                result = {"api_metadata_sha256": digest(root / "ApiMetadata.json")}
            elif phase in ("before", "after"):
                result = control(root / "Control.SLDPRT", raw)
            elif phase == "seal":
                result = seal(root, packet, args.packet_sha256)
            elif phase == "lock":
                result = lock_case(root, packet, args.packet_sha256, case_id)
            else:
                meta = prior(root, "D00", "metadata", args.packet_sha256)
                expected_api = json.loads(checked(root / "ApiMetadata.json", meta["api_metadata_sha256"], root).read_bytes())
                prior(root, case_id if case_id.startswith("H") else "D00", "before", args.packet_sha256)
                case = case_inputs(file, packet, args.packet_sha256, case_id)
                case_root = private if case_id.startswith("H") else root / "Disclosed" / case_id
                case_root.mkdir(parents=True, exist_ok=True)
                previous = case_root / "SavedAuthor.json"
                if phase == "reopen":
                    authored = prior(root, case_id, "author", args.packet_sha256)
                    checked(previous, authored["private_saved_snapshot_sha256"], case_root)
                result = measure_case(phase, case, case_root / "Native", raw, previous, publish, expected_api)
            if not raw.exists():
                write_json(raw, result)
            verify(file, args.packet_sha256)
        publish(**result, stage="passed", passed=True, finished_at=time.time(), private_record_sha256=digest(raw))
    except Exception as error:
        if raw is not None:
            write_json(raw.with_name("Failure.json"), {"error": repr(error)})
        publish(stage="failed", passed=False, finished_at=time.time())
    if raw is not None and case_id.startswith("D") and phase != "seal":
        disclosed = root / "Disclosed" / case_id
        disclosed.mkdir(parents=True, exist_ok=True)
        if raw.exists():
            copyfile(raw, disclosed / (phase + ".json"))
        if raw.with_name("Failure.json").exists():
            copyfile(raw.with_name("Failure.json"), disclosed / (phase + "Failure.json"))
    return {key: state[key] for key in ("case_id", "phase", "stage", "passed")}


def main():
    parser = argparse.ArgumentParser(description="Freeze and execute one native offset-plane source phase without exposing sealed designs")
    modes = parser.add_subparsers(dest="mode", required=True)
    freezer = modes.add_parser("prepare")
    freezer.add_argument("output", type=Path)
    freezer.add_argument("control", type=Path)
    freezer.add_argument("--guest-private-base", required=True)
    for name in ("verify", "run"):
        command = modes.add_parser(name)
        command.add_argument("packet", type=Path)
        command.add_argument("--packet-sha256", required=True)
        if name == "run":
            command.add_argument("case_id", choices=("D00", *SLOT_IDS))
            command.add_argument("phase", choices=PHASES)
    args = parser.parse_args()
    if args.mode == "prepare":
        print(json.dumps(prepare(args), sort_keys=True))
        return 0
    try:
        file = args.packet.resolve(strict=True)
        packet = verify(file, args.packet_sha256)
        if args.mode == "verify":
            print(json.dumps({"verified_packet": args.packet_sha256, "heldout_inputs_read": 0}))
            return 0
        result = run(args, file, packet)
    except Exception:
        result = {"stage": "failed", "passed": False}
    print(json.dumps(result, sort_keys=True))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
