from argparse import ArgumentParser
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path, PureWindowsPath
import re
from secrets import randbelow, token_hex
from subprocess import run
import sys


SCHEMA = "kit.sw2026.private-assigned-material-source-lock.v1"
NATIVE_SCHEMA = "kit.sw2026.assigned-material-native-source.v2"
MANIFEST = "21c49e6b8496267f1b9383f095759b71c9262ca631a7bf32bb96a526184de3bf"
DISCLOSED_JOB = "3289913b17116604a52279a8dca2aba788ec173a2a9f89472605ba699960c477"
DISCLOSED_RESULT = "cb044d2a615d819e8ac642f3eea4bf5f313b8b61c5bd70570e7e3c90895a26f1"
DISCLOSED_SOURCE_LOCK = "c3df77f9b43fb272d16c92da59dc22486e6dd6c8c503c322dcd23fe20960ecba"
DISCLOSED_REVISION = "126a2bd274c898261d5b28e76d0aa55ad5b59ed7"
PRE_WRITER_SRC = "2d2f36df71ef1a9261369ee8fbbc07143a2bb138"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
BUILD = "34.5.2.0604"
CONTROLS = ("ControlBefore", "ControlAfter")
PHASES = ("Author", "Swap", "Depth", "Reopen")
CHECKS = dict(zip(PHASES, (147, 118, 114, 73), strict=True))
STATES = {
    "Author": {"unassigned", "appearance_contrast", "assigned", "after_save"},
    "Swap": {"before", "changed", "after_save"},
    "Depth": {"before", "changed", "after_save"},
    "Reopen": {"before", "after_save"},
}
SAVES = {"Author": "Original.SLDPRT", "Swap": "Swapped.SLDPRT", "Depth": "DepthEdit.SLDPRT"}
TOOLS = {"AuthorAssignedMaterials.py", "MaterialSourceFacts.py", "AuthorCurves.py",
         "AuthorRectangleAnchors.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py"}
COPIED = {"CatalogMetadata01.json", "Control.SLDPRT", "WrapperShape01.json"} | {"Tools/" + name for name in TOOLS}
DISCLOSED_INTENTS = ("D01Corner", "D02Center")
DIMENSIONS = ("width_m", "height_m", "depth_m", "edited_depth_m")
BANDS_UM = (
    ((14500, 20250), (20875, 26750), (7375, 9875), (10425, 12750)),
    ((25375, 31375), (11750, 15750), (10425, 12975), (6475, 8875)),
)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(payload):
    return sha256(payload).hexdigest()


def sha(value):
    require(type(value) is str and re.fullmatch("[0-9a-f]{64}", value), "expected a SHA-256 digest")
    return value


def checked(path, expected):
    require(path.is_file() and not path.is_symlink(), "pinned member is unavailable")
    raw = path.read_bytes()
    require(digest(raw) == sha(expected), "pinned member hash differs")
    return raw


def encode(value):
    return (json.dumps(value, sort_keys=True, allow_nan=False, indent=2) + "\n").encode()


def store(path, raw):
    with path.open("xb") as target:
        target.write(raw)


def process(row):
    identity = row.get("identity", row.get("oracle_identity"))
    require(row["passed"] is True and identity["version_matches"] is True
            and identity["file_version"] == BUILD and identity["sha256"] == ORACLE
            and type(identity["process_id"]) is int and identity["process_id"] > 0
            and type(identity["process_creation_filetime"]) is int and identity["process_creation_filetime"] > 0,
            "native phase did not pass with the exact executable identity")
    return (identity["process_id"], identity["process_creation_filetime"])


def summarize(result, lock, job, job_sha, local=None):
    ids = tuple(case["id"] for case in job["cases"])
    phases = result["phases"]
    expected = (CONTROLS[0], *(f"{slot}/{role}" for slot in ids for role in PHASES), CONTROLS[1])
    require(job["cohort_role"] != "sealed_original" or all(re.fullmatch("Slot[0-9a-f]{32}", slot) for slot in ids),
            "sealed source requires opaque slot names")
    require(result["schema"] == job["schema"] == NATIVE_SCHEMA
            and result["packet_sha256"] == job_sha and result["cohort_role"] == job["cohort_role"]
            and all(result[key] is True for key in ("passed", "controls_healthy", "source_lifecycle_qualified",
                                                    "density_si_hypothesis_confirmed_for_sources", "originals_locked"))
            and result["qualified_writer"] is False and result["writer_outputs"] == result["heldout_credit"] == 0
            and tuple(phases) == expected and len({process(row) for row in phases.values()}) == len(phases)
            == result["distinct_native_processes"] == job["expected_native_processes"] == 10
            and result["source_lock"] == lock and tuple(row["case_id"] for row in lock["originals"]) == ids,
            "terminal native source lifecycle or original lock is incomplete")
    controls = {name: sha(phases[name]["record_sha256"]) for name in CONTROLS}
    if local is not None:
        for name, pin in controls.items():
            checked(local / name / "Record.json", pin)
    subjects = []
    for slot, original in zip(ids, lock["originals"], strict=True):
        prior = None
        notes = {}
        for role in PHASES:
            row = phases[slot + "/" + role]
            record = sha(row["record_sha256"])
            require(set(row["states"]) == STATES[role] and row["numeric_checks"] == CHECKS[role]
                    and not row["dialogs"] and not row["controller_diagnostics"],
                    "native phase observations or numeric coverage differ")
            if role != "Author":
                require(row["open_diagnostics"] == [0, 0] and not row.get("input_mutated")
                        and row["input_sha256_before"] == row["input_sha256_after"] == prior,
                        "immutable native source lineage differs")
            if role in SAVES:
                saved = row["file"]
                prior = sha(saved["sha256"])
                require(saved["diagnostics"] == [True, 0, 0] and saved["bytes"] > 0,
                        "native source save failed")
                if local is not None:
                    target = local / slot / role / SAVES[role]
                    require(Path(saved["path"]).resolve() == target.resolve()
                            and len(checked(target, prior)) == saved["bytes"],
                            "native source bytes differ from their private saved phase")
            if local is not None:
                checked(local / slot / role / "Record.json", record)
            notes[role] = {"record_sha256": record, "numeric_checks": row["numeric_checks"]}
        first = phases[slot + "/Author"]
        require(original["source"] == first["file"] and original["observation_sha256"] == first["record_sha256"]
                and original["request_sha256"] == job["case_intent_sha256"][slot],
                "original did not bind the born-private intent, file and author phase")
        subjects.append({"slot": slot, "original_sha256": sha(first["file"]["sha256"]), "phases": notes})
    require(len(subjects) == len({item["original_sha256"] for item in subjects}) == 2,
            "both independently authored original sources are required")
    return {"subject_locks": subjects, "control_records_sha256": controls, "native_processes": 10,
            "numeric_candidate_checks": 2 * sum(CHECKS.values()), "controls_healthy": True}


def disclosed(manifest_path):
    require(manifest_path.name == "NativeSourcePacket03.json", "expected the original disclosed packet manifest")
    manifest = json.loads(checked(manifest_path, MANIFEST))
    require(manifest["source_revision"] == DISCLOSED_REVISION and manifest["job_sha256"] == DISCLOSED_JOB,
            "disclosed packet authority differs")
    packet = manifest_path.with_suffix("")
    members = manifest["files"]
    names = COPIED | {"Job.json", *("Intent/" + slot + ".json" for slot in DISCLOSED_INTENTS)}
    require(packet.is_dir() and not packet.is_symlink() and len(members) == len(names) == 13
            and {row["path"] for row in members} == names, "disclosed packet member inventory differs")
    files = {}
    for row in members:
        path = packet / row["path"]
        require(path.resolve().is_relative_to(packet.resolve()), "disclosed packet member escaped")
        payload = checked(path, row["sha256"])
        require(len(payload) == row["bytes"], "disclosed packet member length differs")
        files[row["path"]] = payload
    job = json.loads(files["Job.json"])
    require(digest(files["Job.json"]) == DISCLOSED_JOB and job["cohort_role"] == "discovery"
            and tuple(case["id"] for case in job["cases"]) == DISCLOSED_INTENTS and set(job["tools_sha256"]) == TOOLS,
            "disclosed job is outside the pinned scope")
    result = json.loads(checked(packet / "Inspection/Result.json", DISCLOSED_RESULT))
    lock = json.loads(checked(packet / "Inspection/SourceLock.json", DISCLOSED_SOURCE_LOCK))
    summary = summarize(result, lock, job, DISCLOSED_JOB)
    require(summary["numeric_candidate_checks"] == 904, "disclosed candidate coverage differs")
    return {name: files[name] for name in COPIED}, job, result


def new_cases(job):
    require(os.name == "nt", "create private rectangle intents only inside the guest")
    reserved = {case[key] for case in job["cases"] for key in DIMENSIONS}
    cases = []
    for baseline, bands in zip(job["cases"], BANDS_UM, strict=True):
        values = {}
        for key, (low, high) in zip(DIMENSIONS, bands, strict=True):
            available = [value / 1e6 for value in range(low, high + 1, 25) if value / 1e6 not in reserved]
            value = available[randbelow(len(available))]
            values[key] = value
            reserved.add(value)
        cases.append({**baseline, **values, "id": "Slot" + token_hex(16)})
    require(len({case["id"] for case in cases}) == 2, "private slot collision")
    return cases


def guest_root(path):
    import ctypes

    path = PureWindowsPath(path)
    drive_type = ctypes.windll.kernel32.GetDriveTypeW
    drive_type.argtypes = (ctypes.c_wchar_p,)
    drive_type.restype = ctypes.c_uint
    require(path.drive.casefold() == "c:" and path.root == "\\" and len(path.parts) == 2
            and re.fullmatch("KitSealedMaterialSource[0-9]{2,}", path.name)
            and drive_type("C:\\") == 3,
            "reserve a fresh named folder directly on the guest fixed C drive")
    return Path(path)


def preflight(path):
    _, job, native = disclosed(path)
    sample = deepcopy(native)
    sample["packet_sha256"] = "a" * 64
    sample["cohort_role"] = "sealed_original"
    aliases = dict(zip(DISCLOSED_INTENTS, ("Slot" + "0" * 32, "Slot" + "1" * 32), strict=True))
    sample["phases"] = {(aliases[key.split("/")[0]] + "/" + key.split("/")[1]) if "/" in key else key: row
                        for key, row in sample["phases"].items()}
    for row in sample["source_lock"]["originals"]:
        row["case_id"] = aliases[row["case_id"]]
    demo = {
        **job, "cohort_role": "sealed_original",
        "cases": [{**case, "id": aliases[case["id"]]} for case in job["cases"]],
        "case_intent_sha256": {aliases[slot]: pin for slot, pin in job["case_intent_sha256"].items()},
    }
    report = summarize(sample, sample["source_lock"], demo, sample["packet_sha256"])
    require(report["numeric_candidate_checks"] == 904 and "states" not in repr(report)
            and all(set(row) == {"slot", "original_sha256", "phases"} for row in report["subject_locks"]),
            "synthetic receipt leaked raw source observations")
    phase = next(key for key in sample["phases"] if key.endswith("/Swap"))
    sample["phases"][phase]["numeric_checks"] -= 1
    try:
        summarize(sample, sample["source_lock"], demo, sample["packet_sha256"])
    except ValueError:
        return {"passed": True, "verified_disclosed_input_members": 13, "checked_disclosed_phases": 10,
                "verified_disclosed_numeric_checks": 904, "host_private_inputs": 0,
                "new_native_processes": 0, "altered_synthetic_phase_refused": True}
    raise ValueError("synthetic coverage regression did not fail")


def seal(args):
    require(os.name == "nt", "private source authoring belongs to the root Windows oracle")
    require(type(args.revision) is str and re.fullmatch("[0-9a-f]{40}", args.revision),
            "committed pre-writer launcher revision required")
    tool_sha = sha(args.tool_sha256)
    checked(Path(__file__).resolve(), tool_sha)
    copied, old_job, _ = disclosed(args.manifest)
    local = guest_root(args.private_root)
    require(not args.receipt.resolve().is_relative_to(local.resolve())
            and not args.receipt.exists() and not args.receipt.is_symlink(),
            "reserve an unused aggregate receipt outside the private source directory")
    local.mkdir(exist_ok=False)
    cases = new_cases(old_job)
    intent = {"Intent/" + case["id"] + ".json": encode(case) for case in cases}
    hashes = {case["id"]: digest(intent["Intent/" + case["id"] + ".json"]) for case in cases}
    job = {**old_job, "cohort_role": "sealed_original", "cases": cases, "case_intent_sha256": hashes}
    files = copied | intent | {"Job.json": encode(job)}
    for relative, payload in files.items():
        path = local / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        store(path, payload)
    job_sha = digest(files["Job.json"])
    private = encode({"locked_at_utc": datetime.now(timezone.utc).isoformat(), "nonce": token_hex(32),
                      "launcher_revision": args.revision, "sdk_tree_before_material_writer": PRE_WRITER_SRC,
                      "tool_sha256": tool_sha, "members": {key: digest(value) for key, value in files.items()},
                      "job_sha256": job_sha, "prior_disclosed_result_sha256": DISCLOSED_RESULT})
    prelock = local / "PrivatePreflight.json"
    store(prelock, private)
    with (local / "NativeAuthor.log").open("xb") as log:
        command = (sys.executable, "-E", "-B", str(local / "Tools/AuthorAssignedMaterials.py"))
        arguments = (str(local / "Job.json"), "--packet-sha256", job_sha)
        require(run((*command, "verify", *arguments), stdout=log, stderr=log, check=False, cwd=local).returncode == 0,
                "private native author preflight failed")
        require(run((*command, "run", *arguments), stdout=log, stderr=log, check=False, cwd=local).returncode == 0,
                "private native source lifecycle failed")
    raw = local / "Inspection"
    terminal = (raw / "Result.json").read_bytes()
    lock = (raw / "SourceLock.json").read_bytes()
    report = summarize(json.loads(terminal), json.loads(lock), job, job_sha, raw)
    require(all(checked(local / name, digest(payload)) == payload for name, payload in files.items())
            and checked(prelock, digest(private)) == private, "private input custody changed during authoring")
    receipt = {
        "schema": SCHEMA, "passed": True,
        "launcher_revision": args.revision, "launcher_sha256": tool_sha, "pre_writer_sdk_tree": PRE_WRITER_SRC,
        "disclosed_packet_sha256": MANIFEST, "disclosed_native_result_sha256": DISCLOSED_RESULT,
        "disclosed_source_lock_sha256": DISCLOSED_SOURCE_LOCK, "private_intent_commitment_sha256": digest(private),
        "primary_native_result_sha256": digest(terminal), "private_original_source_lock_sha256": digest(lock),
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "protected_payloads_exported": 0, "writer_outputs": 0, "heldout_comparison_credit": 0, **report,
    }
    payload = encode(receipt)
    store(args.receipt, payload)
    return {"passed": True, "receipt_sha256": digest(payload), "native_processes": report["native_processes"],
            "numeric_candidate_checks": report["numeric_candidate_checks"]}


def main():
    parser = ArgumentParser()
    actions = parser.add_subparsers(dest="action", required=True)
    check = actions.add_parser("preflight")
    check.add_argument("manifest", type=Path)
    start = actions.add_parser("seal")
    start.add_argument("manifest", type=Path)
    start.add_argument("--tool-sha256", required=True)
    start.add_argument("--revision", required=True)
    start.add_argument("--private-root", type=Path, required=True)
    start.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "preflight":
        result = preflight(args.manifest)
    else:
        try:
            result = seal(args)
        except Exception:
            print('{"passed":false,"diagnostic":"sealed_source_authoring_refused"}')
            return 3
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
