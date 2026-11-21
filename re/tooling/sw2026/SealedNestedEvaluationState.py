from __future__ import annotations

import ctypes
import json
import re
from pathlib import Path, PurePosixPath

from AuthorCurves import digest, require
from FreezeSealedNestedEvaluation import FIRST_NATIVE, REPEATED_PACKET, SCHEMA, SOURCE_LOCK, SOURCE_PHASE, TOOLS, WRITER_EVIDENCE, WRITER_REVISION, qualify_discovery
from NestedAssemblySourcePlan import ORACLE, checked, valid_sha
from SealedNeutralNestedProfile import EVIDENCE_ROLES, PROFILE, WORKER, read_evidence
from RunSealedNestedSourcePhase import load_author, opaque_identity, read_guest_case, source_inputs


SCRIPT = Path(__file__).resolve()


def verify(path, sha):
    root = path.parent
    require(path.name == "Evaluation.json" and checked(path, sha, root) == path, "sealed evaluation manifest is not pinned")
    packet = json.loads(path.read_bytes())
    profile = packet.get("writer_profile")
    require(packet["schema"] == SCHEMA and packet["oracle_sha256"] == ORACLE and profile in (None, PROFILE) and
            packet["source_lock_sha256"] == SOURCE_LOCK and packet["source_phase_sha256"] == SOURCE_PHASE and
            packet["host_heldout_payloads_read"] == 0 and packet["sealed_results"] is True and packet["native_acceptance"] is False,
            "unexpected sealed writer evaluation identity")
    tools = root / "Tools"
    require(SCRIPT.parent == tools and set(packet["tools_sha256"]) == set(TOOLS) == {item.name for item in tools.glob("*.py")}, "run exactly the frozen sealed evaluator")
    for name, wanted in packet["tools_sha256"].items():
        checked(tools / name, wanted, tools)
    lock = json.loads(checked(root / "SourceLock.json", SOURCE_LOCK, root).read_bytes())
    require(lock["passed"] is True and len(lock["slots"]) == 2 and all(row["heldout_source_locked"] is True for row in lock["slots"]), "sealed source locks are incomplete")
    source_phase = json.loads(checked(root / "SourcePhase.json", SOURCE_PHASE, root).read_bytes())
    require(source_phase["source_deck_sha256"] == lock["source_deck_sha256"], "sealed source phase custody differs")
    manifest = json.loads(checked(root / "CodeManifest.json", packet["code_manifest_sha256"], root).read_bytes())
    revision = packet["writer_revision"]
    require(manifest["schema"] == "kit.sw2026.frozen-nested-writer-code.v1" and manifest["writer_revision"] == revision
            and re.fullmatch(r"[0-9a-f]{40}", revision), "unexpected frozen code schema")
    code_root = root / "CodeRoot"
    if profile == PROFILE:
        sdk_tree = manifest["sdk_tree"]
        require(re.fullmatch(r"[0-9a-f]{40}", sdk_tree) and set(packet["disclosed_evidence"]) == set(EVIDENCE_ROLES),
                "sealed neutral writer snapshot or evidence roles are incomplete")
        single, repeated = (read_evidence(root / role, packet["disclosed_evidence"][role], revision, sdk_tree, SOURCE_LOCK)
                            for role in EVIDENCE_ROLES)
        require(len(set(single["processes"] + repeated["processes"])) == 8
                and repeated["expanded"] > single["expanded"] >= 2 and repeated["leaves"] > single["leaves"] == 1
                and single["worker_sha256"] == repeated["worker_sha256"] == manifest["files_sha256"][WORKER],
                "disclosed native trials do not bind distinct processes and the exact guarded neutral worker")
    else:
        require(revision == WRITER_REVISION and packet["writer_evidence_sha256"] == WRITER_EVIDENCE,
                "unexpected legacy writer proof")
        evidence = json.loads(checked(root / "WriterEvidence.json", WRITER_EVIDENCE, root).read_bytes())
        require(packet["writer_tool_sha256"] == evidence["writer_tool_sha256"], "sealed writer fingerprints differ from disclosed proof")
        for file, wanted, native_packet in (("FirstDiscovery.json", FIRST_NATIVE, None), ("RepeatedDiscovery.json", packet["repeated_discovery_sha256"], REPEATED_PACKET)):
            result = json.loads(checked(root / file, wanted, root).read_bytes())
            qualify_discovery(result, native_packet or result["packet_sha256"], evidence["writer_tool_sha256"])
        for name, wanted in evidence["writer_tool_sha256"].items():
            checked(code_root / "re/tooling/sw2026" / name, wanted, code_root)
    for name, wanted in manifest["files_sha256"].items():
        relative = PurePosixPath(name)
        require(not relative.is_absolute() and ".." not in relative.parts and relative.suffix == ".py", "frozen code entry escaped its source closure")
        checked(code_root / name, wanted, code_root)
    require(set(manifest["files_sha256"]) == {item.relative_to(code_root).as_posix() for item in code_root.rglob("*.py")}, "frozen code source closure changed")
    return packet, lock, source_phase


def fixed_directory(value):
    path = Path(value)
    drive_type = ctypes.windll.kernel32.GetDriveTypeW
    drive_type.argtypes, drive_type.restype = (ctypes.c_wchar_p,), ctypes.c_uint
    require(re.fullmatch(r"[A-Za-z]:", path.drive) and path.resolve() == path and drive_type(path.anchor) == 3,
            "private artifacts require an ordinary fixed guest-local path")
    return path


def private_trial(packet, sha, slot, trial):
    base = fixed_directory(packet["guest_private_base"])
    root = base / sha / f"Slot{slot:02d}" / trial
    require(root.resolve() == root, "private trial escaped its canonical owned path")
    root.mkdir(parents=True, exist_ok=True)
    return root


def source_snapshot(packet, lock, source_phase, slot):
    from AuthorNestedAssemblySources import file_paths

    original = Path(packet["source_phase_guest"])
    checked(original, SOURCE_PHASE, original.parent)
    require(json.loads(original.read_bytes()) == source_phase, "the guest source packet differs from the frozen public packet")
    row, = [item for item in lock["slots"] if item["slot"] == slot]
    source_root = fixed_directory(source_phase["guest_private_base"]) / SOURCE_PHASE / f"Slot{slot:02d}" / row["trial"]
    require(source_root.resolve(strict=True) == source_root and source_root.is_dir(), "the locked native source trial is unavailable")
    public_record = original.parent / "Progress" / f"Slot{slot:02d}" / row["trial"] / "lock/1/Record.json"
    source_record = json.loads(checked(public_record, row["source_lock_sha256"], original.parent).read_bytes())
    require(source_record["stage"] == "locked" and source_record["passed"] is True and source_record["heldout_source_locked"] is True and
            source_record["native_artifact_manifest_sha256"] == row["native_artifact_manifest_sha256"], "sealed source native lock does not qualify")
    _, sealed_file, expected = source_inputs(source_phase)
    require(expected == lock["heldout_spec_sha256"], "sealed source specification identity differs")
    case = read_guest_case(sealed_file, expected, slot)
    snapshot = load_author(source_root, row, case, file_paths(source_root / "Native", case))
    return case, snapshot


def prior_phase(public, phase, attempt, sha, slot, trial, identity=False):
    file = public / phase / str(attempt) / "Record.json"
    state = json.loads(file.read_bytes())
    require(state["passed"] is True and state["stage"] == "passed" and state["packet_sha256"] == sha and state["slot"] == slot and
            state["trial"] == trial and state["phase"] == phase and state["attempt"] == attempt, "sealed evaluation prerequisite is not qualified")
    if identity:
        opaque_identity(state["identity"])
    return state


def load_build(private, public, sha, slot, trial, writer_revision):
    state = prior_phase(public, "build", 1, sha, slot, trial)
    path = checked(private / "BuildLock.json", state["build_lock_sha256"], private)
    lock = json.loads(path.read_bytes())
    require(lock["packet_sha256"] == sha and lock["writer_revision"] == writer_revision and lock["runtime_file_read_attempts"] == 0 and
            lock["two_process_byte_identity"] is True, "sealed generated build does not qualify")
    request = json.loads(checked(private / "Request.json", lock["request_sha256"], private).read_bytes())
    prediction = json.loads(checked(private / "Expected.json", lock["prediction_sha256"], private).read_bytes())
    for name, row in lock["files"].items():
        require(valid_sha(row["sha256"]) and name == prediction["definitions"][name]["file"].rsplit(".", 1)[0], "sealed generated dependency identity differs")
        checked(private / "FrozenGenerated" / row["file"], row["sha256"], private)
    return lock, request, prediction
