from hashlib import sha256
import json
from pathlib import Path, PurePosixPath, PureWindowsPath


SCHEMA = "kit.sw2026.thin-revolve-independent-evaluation.v1"
WRITER = "c34a607e40519fe78eea5b3c86288c545c77c886"
WRITER_TREE = "9703887934a847918d0d3ebda4183bcd09b692d6"
LOCK_REVISION = "35c607164409bff6fe2222358ac1e8b6da981782"
LOCK_RELATIVE = "re/solidworks/measurements/2026/RevolveThinHeldoutSourceLock01.json"
LOCK_SHA = "e81db7caf2db600543f6f85b61b3a47a27cfd4b670f8e6a55f45dc79e6637653"
DISCLOSURE_SHA = "cdada047b9f9bd7be97b62383c07bcee06a527a69152af83d932801e2a556b5c"
DISCLOSURE_JOB_SHA = "f00ddbfe7e7a9e6ba0f63c86129946f2bf7d58811d760bb5b1812520864648ea"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
VERSION = "34.5.2.0604"
ORIGINALS = PureWindowsPath(r"C:\KitSdkCandidates\RevolveThinHeldout01")
SPEC = PureWindowsPath(r"C:\KitSdkCandidates\RevolveThinHeldout01Author\Spec.json")
STANDALONE = ("RunThinHeldout.py", "ThinHeldoutPacket.py", "ThinHeldoutNative.py")
SWROOT = "re/tooling/sw2026/"
THINROOT = SWROOT + "revolve/ThinArchive/"
CASES = tuple(f"Slot{index:02}" for index in range(1, 5))
MODES = {"one", "opposite", "midplane", "two"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return sha256(raw).hexdigest()


def checked(path, pin):
    require(path.is_file() and not path.is_symlink(), "missing or indirect frozen input")
    raw = path.read_bytes()
    require(digest(raw) == pin, "frozen input digest differs")
    return raw


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def publish(path, raw):
    with path.open("xb") as output:
        output.write(raw)
    return digest(raw)


def source_lock(raw):
    require(digest(raw) == LOCK_SHA, "pre-writer source lock digest differs")
    lock = json.loads(raw)
    require(lock["schema"] == "kit.sw2026.revolve-family-source-lock.v1"
            and (lock["family"], lock["split"]) == ("thin", "heldout")
            and lock["oracle_sha256"] == ORACLE and lock["oracle_build"] == VERSION
            and lock["fresh_processes"] == lock["distinct_processes"] == 14
            and lock["writer_output_count"] == 0 and lock["heldout_writer_acceptance"] is False
            and lock["passed"] and lock["control-before"]["passed"] and lock["control-after"]["passed"]
            and lock["idle_after"] and lock["inputs_unchanged"] and lock["tools_unchanged"]
            and tuple(row["case"] for row in lock["sources"]) == CASES
            and all(row["passed"] and tuple(p["phase"] for p in row["phases"]) == ("author", "reopen", "edited-reopen")
                    and all(p["passed"] and p["checks"] == p["checks_passed"] for p in row["phases"])
                    for row in lock["sources"]), "pre-writer source cohort is incomplete")
    return lock


def disclosure(raw):
    require(digest(raw) == DISCLOSURE_SHA, "disclosed native result digest differs")
    result = json.loads(raw)
    require(result["schema"] == "kit.sw2026.thin-generated-disclosure-result.v1"
            and result["writer_revision"] == WRITER and result["writer_sdk_tree"] == WRITER_TREE
            and result["job_sha256"] == DISCLOSURE_JOB_SHA
            and result["oracle_sha256"] == ORACLE and result["oracle_build"] == VERSION
            and result["fresh_processes"] == result["distinct_processes"] == 18
            and result["passed"] and result["control-before"]["passed"] and result["control-after"]["passed"]
            and result["idle_after"] and result["inputs_unchanged"] and len(result["cases"]) == 4
            and all(row["passed"] for row in result["cases"]), "exact writer lacks a passing disclosed baseline")
    return result


def guest_work(value):
    path = PureWindowsPath(value)
    require(path.is_absolute() and path.drive.casefold() == "c:" and path.parent == ORIGINALS.parent
            and path.name.startswith("SdkThinHeldoutEvaluation")
            and path.name.removeprefix("SdkThinHeldoutEvaluation").isdigit(), "invalid isolated guest workspace")
    return path


def packet_data(packet, pin):
    manifest = json.loads(checked(packet / "Manifest.json", pin))
    require(manifest["schema"] == SCHEMA and manifest["writer"] == WRITER
            and manifest["writer_src_tree"] == WRITER_TREE and manifest["source_lock_revision"] == LOCK_REVISION
            and manifest["source_lock_sha256"] == LOCK_SHA and manifest["disclosed_sha256"] == DISCLOSURE_SHA
            and manifest["oracle_sha256"] == ORACLE and set(manifest["supervisor"]) == set(STANDALONE)
            and manifest["private_inputs_read_during_freeze"] == 0, "wrong frozen thin evaluation job")
    for name, sha in manifest["supervisor"].items():
        checked(packet / name, sha)
    lock = source_lock(checked(packet / "SourceLock.json", LOCK_SHA))
    disclosure(checked(packet / "DisclosedNative.json", DISCLOSURE_SHA))
    checked(packet / "DisclosedJob.json", DISCLOSURE_JOB_SHA)
    require(manifest["source_lock_finished_at"] == lock["finished_at"] < manifest["writer_commit_at"]
            <= manifest["frozen_at"], "source lock did not predate the exact generated writer")
    checked(packet / "Control.SLDPRT", lock["control_sha256"])
    return manifest, lock, Path(guest_work(manifest["guest_work"]))


def archive_path(name):
    path = PurePosixPath(name)
    require(not path.is_absolute() and path.as_posix() == name and ".." not in path.parts
            and "\\" not in name and ":" not in name
            and (name.startswith("src/") or name.startswith(SWROOT) and name.endswith(".py")),
            "unexpected writer package member")
    return path
