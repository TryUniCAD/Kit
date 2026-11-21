from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from hashlib import sha256
from pathlib import Path, PureWindowsPath
from shutil import copyfile

from AuthorCurves import Recorder, digest, require, write_json
from AuthorNestedAssemblySources import author_case, file_paths, reopen_case
from NestedAssemblySourcePlan import CONTROL_SHA, DECK_SCHEMA, ORACLE, PARAMETERS, SOURCE_LOCK, SPEC_SCHEMA, TOOL_FILES, checked, valid_sha, validate_case


SCRIPT = Path(__file__).resolve()
TOOLS = (*TOOL_FILES, SCRIPT.name)
SCHEMA = "kit.sw2026.sealed-nested-source-phases.v1"
PHASES = ("before", "author", "reopen", "after", "lock")
OBSERVER = "99262334a240e6caedc6129118ae09fae1fd767a0012cd03ab4f86ada543c1bf"


def guest_path(value):
    path = PureWindowsPath(value)
    require(path.is_absolute() and ".." not in path.parts, "provide an absolute Windows guest path")
    return path


def verify(packet_path, sha):
    root = packet_path.parent
    require(packet_path.name == "SealedPhases.json" and checked(packet_path, sha, root) == packet_path, "unbound sealed phase packet")
    packet = json.loads(packet_path.read_bytes())
    require(packet["schema"] == SCHEMA and packet["oracle_sha256"] == ORACLE and packet["control_sha256"] == CONTROL_SHA and
            valid_sha(packet["source_deck_sha256"]) and packet["tools_sha256"]["ObserveAssemblyLoad.py"] == OBSERVER,
            "unexpected source or observer identity")
    require(guest_path(packet["source_deck"]).name == "Deck.json", "original source deck name differs")
    private = guest_path(packet["guest_private_base"])
    require(re.fullmatch(r"[A-Za-z]:", private.drive) and len(private.parts) > 1, "choose a private guest-local directory")
    tools = (root / "Tools").resolve(strict=True)
    require(tools == SCRIPT.parent and tools.is_relative_to(root) and set(packet["tools_sha256"]) == set(TOOLS), "run the frozen phase tooling")
    for name, wanted in packet["tools_sha256"].items():
        checked(tools / name, wanted, tools)
    return packet


def prepare(args):
    root = args.output.resolve()
    require(root.parent.is_dir() and not root.exists() and not root.is_relative_to(SCRIPT.parents[3]), "choose an unused private phase packet")
    source = guest_path(args.source_deck)
    directory = guest_path(args.guest_private_base)
    require(source.name == "Deck.json" and valid_sha(args.source_deck_sha256), "provide the original source deck fingerprint")
    require(re.fullmatch(r"[A-Za-z]:", directory.drive) and len(directory.parts) > 1, "choose a private guest-local directory")
    require(digest(SCRIPT.with_name("ObserveAssemblyLoad.py")) == OBSERVER, "freeze the corrected progress observer")
    root.mkdir()
    tools = root / "Tools"
    tools.mkdir()
    hashes = {}
    for name in TOOLS:
        target = tools / name
        copyfile(SCRIPT.parent / name, target)
        hashes[name] = digest(target)
    path = root / "SealedPhases.json"
    write_json(path, {"schema": SCHEMA, "source_deck": str(source), "source_deck_sha256": args.source_deck_sha256,
                      "guest_private_base": str(directory), "oracle_sha256": ORACLE, "control_sha256": CONTROL_SHA, "tools_sha256": hashes})
    sha = digest(path)
    subprocess.run([sys.executable, "-B", str(tools / SCRIPT.name), "verify", str(path), "--packet-sha256", sha],
                   check=True, capture_output=True, timeout=25)
    return {"packet": str(path), "packet_sha256": sha, "tools_sha256": hashes}


def source_inputs(packet):
    source = Path(packet["source_deck"]).resolve(strict=True)
    checked(source, packet["source_deck_sha256"], source.parent)
    deck = json.loads(source.read_bytes())
    require(deck["schema"] == DECK_SCHEMA and deck["oracle_sha256"] == ORACLE and deck["control_sha256"] == CONTROL_SHA and
            deck["reference_source_lock_sha256"] == SOURCE_LOCK and deck["heldout_results_sealed"] is True and
            valid_sha(deck["holdouts_sha256"]), "unexpected sealed source deck")
    inputs = (source.parent / "Inputs").resolve(strict=True)
    require(inputs.is_relative_to(source.parent), "source inputs escaped the original deck")
    seed = checked(inputs / "Seed.SLDPRT", CONTROL_SHA, inputs)
    return seed, inputs / "Holdouts.json", deck["holdouts_sha256"]


def read_guest_case(source, expected, slot):
    sealed = checked(source, expected, source.parent)
    data = json.loads(sealed.read_bytes())
    require(set(data) == {"schema", "cases"} and data["schema"] == SPEC_SCHEMA and len(data["cases"]) == 2, "unexpected sealed case set")
    case = validate_case(data["cases"][slot - 1])
    require(case["split"] == "heldout" and case["name"].startswith(f"N0{slot + 2}"), "unexpected sealed slot assignment")
    return case


def local_trial(packet, packet_sha, slot, trial):
    import ctypes

    base = Path(packet["guest_private_base"])
    drive_type = ctypes.windll.kernel32.GetDriveTypeW
    drive_type.argtypes = (ctypes.c_wchar_p,)
    drive_type.restype = ctypes.c_uint
    require(base.resolve() == base and drive_type(base.anchor) == 3, "native artifacts require a fixed guest-local drive")
    directory = base / packet_sha / f"Slot{slot:02d}" / trial
    require(directory.resolve() == directory, "guest-local trial must use its owned canonical path")
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def opaque_identity(identity):
    view = {key: identity[key] for key in ("process_id", "process_creation_filetime", "file_version", "sha256")}
    require(type(view["process_id"]) is int and view["process_id"] > 0 and type(view["process_creation_filetime"]) is int and
            view["process_creation_filetime"] > 0 and view["file_version"] == "34.5.2.0604" and view["sha256"] == ORACLE,
            "sealed phase identity differs from the pinned oracle")
    return view


def artifact_manifest(directory, saved, paths):
    require(set(saved) == set(paths), "sealed source dependency closure differs")
    manifests = {}
    for name, path in paths.items():
        item = saved[name]
        require(item["status"] == [True, 0, 0] and checked(path, item["sha256"], directory).stat().st_size == item["bytes"], "sealed native artifact differs from save")
        manifests[path.name] = {"sha256": item["sha256"], "bytes": item["bytes"]}
    return manifests


def value_hash(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


class PrivateRecorder(Recorder):
    def __init__(self, path, job, publish):
        self.publish = publish
        self.last_public = float("-inf")
        super().__init__(path, job)

    def flush(self):
        super().flush()
        now = time.monotonic()
        if now - self.last_public >= 1.0:
            self.publish(progress_at=time.time())
            self.last_public = now


def measure_control(seed, raw, publish):
    from InspectFresh import healthy, inspect

    result = {}

    def progress():
        write_json(raw, result)
        identity = result.get("oracle_identity")
        progress_row = {"stage": "control", "progress_at": time.time()}
        if identity and identity["version_matches"] and identity["sha256"] == ORACLE:
            progress_row["identity"] = opaque_identity(identity)
        publish(**progress_row)

    inspect(seed, result=result, checkpoint=progress, parameter_names=PARAMETERS)
    require(result["sha256"] == digest(seed) == CONTROL_SHA and result.get("oracle_identity", {}).get("sha256") == ORACLE and healthy(result),
            "sealed source control failed")
    return {"oracle_identity": result["oracle_identity"]}


def prior_phase(public_root, phase, attempt, packet_sha, slot, trial):
    path = public_root / phase / str(attempt) / "Record.json"
    require(path.resolve(strict=True) == path and path.is_file(), "sealed prerequisite record changed path")
    state = json.loads(path.read_bytes())
    require(state["stage"] == "passed" and state["passed"] is True and state["packet_sha256"] == packet_sha and state["phase"] == phase and
            state["slot"] == slot and state["trial"] == trial and state["attempt"] == attempt, "sealed prerequisite phase failed or does not match")
    opaque_identity(state["identity"])
    return state


def load_author(private, saved_phase, case, paths):
    snapshot_path = private / "SavedAuthor.json"
    saved = json.loads(checked(snapshot_path, saved_phase["private_saved_snapshot_sha256"], private).read_bytes())
    require(saved["case"] == case and saved["artifact_manifest"] == artifact_manifest(private / "Native", saved["result"]["saved_files"], paths),
            "saved author checkpoint disagrees with the sealed occurrence closure")
    require(value_hash(saved["artifact_manifest"]) == saved_phase["native_artifact_manifest_sha256"], "sealed artifact manifest hash differs")
    return saved


def measure_case(phase, seed, private, case, previous, raw, publish):
    import Swapp
    from AuthorCurves import CurveAuthor
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity

    directory = private / "Native"
    paths = file_paths(directory, case)
    if phase == "author":
        directory.mkdir(exist_ok=False)
    result = {}
    controller = None
    recorder = PrivateRecorder(raw, {"case": case, "phase": phase}, publish)
    with AssemblyLoadMonitor() as monitor:
        try:
            publish(stage="starting_oracle")
            recorder.call("verify idle oracle", Swapp.sweep)
            controller = recorder.call("launch fresh owned oracle", Swapp.Sw)
            identity = recorder.call("verify executable version and SHA-256", application_identity, controller.app)
            require(identity["version_matches"] and controller.revision == "34.5.2", "unexpected SOLIDWORKS build")
            result["oracle_identity"] = identity
            publish(stage="native_work", identity=opaque_identity(identity))
            author = CurveAuthor(controller.app, recorder, Swapp)
            if phase == "author":
                author_case(author, controller, case, paths, seed, directory, result)
                artifacts = artifact_manifest(directory, result["saved_files"], paths)
                snapshot = private / "SavedAuthor.json"
                write_json(snapshot, {"case": case, "result": result, "artifact_manifest": artifacts})
                publish(stage="files_saved", native_artifact_manifest_sha256=value_hash(artifacts), private_saved_snapshot_sha256=digest(snapshot))
            else:
                reopen_case(author, controller, case, paths, previous["result"], result)
        except Exception as error:
            recorder.failure(error)
            raise
        finally:
            if controller is not None:
                publish(stage="closing_oracle")
                controller.close()
                result["controller_diagnostics"] = controller.diagnostics
        result["dialogs"] = monitor.log
        result["progress_windows"] = monitor.progress
    require(not result["dialogs"] and not result["controller_diagnostics"] and not recorder.data["cleanup_errors"], "native phase reported a dialog or cleanup problem")
    saved = (result if phase == "author" else previous["result"])["saved_files"]
    artifacts = artifact_manifest(directory, saved, paths)
    recorder.data.update(result=result, passed=True, finished_at=time.time())
    recorder.flush()
    return {"oracle_identity": result["oracle_identity"], "native_artifact_manifest_sha256": value_hash(artifacts)}


def lock_source(local, public_root, packet_sha, slot, trial, attempt, case):
    phases = PHASES[:4]
    attempts = (1, 1, attempt, attempt)
    observations = [prior_phase(public_root, phase, number, packet_sha, slot, trial) for phase, number in zip(phases, attempts, strict=True)]
    identities = [opaque_identity(row["identity"]) for row in observations]
    require(len({row["process_creation_filetime"] for row in identities}) == 4 and
            all(first["finished_at"] <= second["started_at"] for first, second in zip(observations, observations[1:])), "sealed phases are not distinct and bracketed in order")
    for name, number, row in zip(phases, attempts, observations, strict=True):
        checked(local / name / str(number) / "Private.json", row["private_record_sha256"], local)
    author, reopen = observations[1:3]
    saved = load_author(local, author, case, file_paths(local / "Native", case))
    native_sha = value_hash(saved["artifact_manifest"])
    require(native_sha == author["native_artifact_manifest_sha256"] == reopen["native_artifact_manifest_sha256"], "sealed source reopens a different artifact set")
    return {"native_artifact_manifest_sha256": native_sha, "private_saved_snapshot_sha256": author["private_saved_snapshot_sha256"],
            "private_phase_records_sha256": [row["private_record_sha256"] for row in observations], "oracle_processes": identities,
            "heldout_source_locked": True}


def run(args, packet_path, packet):
    require(os.name == "nt", "native sealed phases run in the Windows guest")
    slot, phase, trial, attempt = args.slot, args.phase, args.trial, args.attempt
    require(re.fullmatch(r"[A-Za-z0-9]{1,16}", trial) and type(attempt) is int and 1 <= attempt <= 99 and
            (attempt == 1 or phase in ("reopen", "after", "lock")), "invalid phase attempt")
    public_root = packet_path.parent / "Progress" / f"Slot{slot:02d}" / trial
    output = public_root / phase / str(attempt)
    require(output.resolve().is_relative_to(packet_path.parent), "public phase directory escaped its packet")
    output.mkdir(parents=True, exist_ok=False)
    path = output / "Record.json"
    state = {"schema": SCHEMA, "packet_sha256": args.packet_sha256, "source_deck_sha256": packet["source_deck_sha256"],
             "slot": slot, "trial": trial, "phase": phase, "attempt": attempt, "stage": "verifying", "passed": False, "started_at": time.time()}

    def publish(**changes):
        state.update(changes)
        write_json(path, state)

    publish()
    raw = None
    try:
        private = local_trial(packet, args.packet_sha256, slot, trial)
        private_run = private / phase / str(attempt)
        require(private_run.resolve() == private_run, "private phase escaped its owned trial")
        private_run.mkdir(parents=True, exist_ok=False)
        raw = private_run / "Private.json"
        seed, holdout_file, expected = source_inputs(packet)
        if phase in ("before", "after"):
            result = measure_control(seed, raw, publish)
        else:
            case = read_guest_case(holdout_file, expected, slot)
            if phase == "lock":
                result = lock_source(private, public_root, args.packet_sha256, slot, trial, attempt, case)
            else:
                prior_phase(public_root, "before", 1, args.packet_sha256, slot, trial)
                previous = None
                if phase == "reopen":
                    authored = prior_phase(public_root, "author", 1, args.packet_sha256, slot, trial)
                    previous = load_author(private, authored, case, file_paths(private / "Native", case))
                result = measure_case(phase, seed, private, case, previous, raw, publish)
        if not raw.exists():
            write_json(raw, result)
        if "oracle_identity" in result:
            result["identity"] = opaque_identity(result.pop("oracle_identity"))
        publish(**result, stage="locked" if phase == "lock" else "passed", passed=True, finished_at=time.time(), private_record_sha256=digest(raw))
    except Exception as error:
        if raw is not None:
            if not raw.exists():
                write_json(raw, {"error": repr(error)})
            else:
                write_json(raw.with_name("Failure.json"), {"error": repr(error)})
        publish(stage="failed", finished_at=time.time())
    return {key: state[key] for key in ("slot", "phase", "stage", "passed")}


def main():
    parser = argparse.ArgumentParser(description="Freeze or run one private Windows phase of a sealed nested source case")
    commands = parser.add_subparsers(dest="command", required=True)
    freezer = commands.add_parser("prepare")
    freezer.add_argument("output", type=Path)
    for flag in ("--source-deck", "--source-deck-sha256", "--guest-private-base"):
        freezer.add_argument(flag, required=True)
    for mode in ("verify", "run"):
        command = commands.add_parser(mode)
        command.add_argument("packet", type=Path)
        command.add_argument("--packet-sha256", required=True)
        if mode == "run":
            command.add_argument("slot", type=int, choices=(1, 2))
            command.add_argument("trial")
            command.add_argument("phase", choices=PHASES)
            command.add_argument("--attempt", type=int, default=1)
    args = parser.parse_args()
    if args.command == "prepare":
        print(json.dumps(prepare(args), sort_keys=True))
        return 0
    path = args.packet.resolve(strict=True)
    packet = verify(path, args.packet_sha256)
    if args.command == "verify":
        print(json.dumps({"verified_packet": args.packet_sha256}))
        return 0
    try:
        result = run(args, path, packet)
    except Exception:
        result = {"slot": args.slot, "phase": args.phase, "stage": "failed", "passed": False}
    print(json.dumps(result))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
