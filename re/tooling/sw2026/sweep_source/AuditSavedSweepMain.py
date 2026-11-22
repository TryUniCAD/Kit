from argparse import ArgumentParser
from base64 import b64decode, b64encode
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from subprocess import run
import sys
from tarfile import open as open_tar
from tempfile import TemporaryDirectory
from zlib import ZLIB_RUNTIME_VERSION

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
BASE = "ab4c5b98b5fdb7b49146601ffc5731aa0b6a095d"
BASE_SRC = "31a7a096ee8ba9efdb78042bfa25a7d9aaf20e96"
SHARED = "f59507fccdd5907954634489f54ab1364f44580e"
SHARED_PARENT = "fd2de84904eb048347413e75e51d75ed33d49c9f"
SHARED_SRC = "cb9ffb438192f7d803c8ad38428a634ee984ed51"
RESEARCH = "daebc428bffb80ab45ca6f2ddb17984c8f155f7a"
PRIOR_REPLAY = "bfc8631fc701568435fcf68ee3f8881b6bdc632a0886a864578c38ecf9262da7"
LOCK = "563aef5da24478ab83b881092561dd09066ad9b8e3999ca1da106e00e22420ca"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
ROLES = (("original", ""), ("section", "SectionEdit"), ("path", "PathEdit"))


def demand(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return sha256(raw).hexdigest()


def checked(path, expected):
    demand(path.is_file() and not path.is_symlink(), f"missing regular disclosed file {path.name}")
    result = path.read_bytes()
    demand(digest(result) == expected, f"disclosed digest differs for {path.name}")
    return result


def git(*arguments):
    return run(("git", "-C", str(ROOT), *arguments), check=True, capture_output=True).stdout


def scratch_sdk(directory):
    demand(git("rev-parse", BASE + ":src").decode().strip() == BASE_SRC
           and git("rev-parse", SHARED + ":src").decode().strip() == SHARED_SRC,
           "pinned codec source tree differs")
    paths = git("diff", "--name-only", SHARED_PARENT, SHARED, "--",
                "src/convert/adapters/solidworks/Archive").decode().splitlines()
    demand(len(paths) == 17 and all(path.endswith(".py") for path in paths),
           "shared archive source closure differs")
    with open_tar(fileobj=BytesIO(git("archive", BASE, "src"))) as archive:
        archive.extractall(directory, filter="data")
    overlay = {}
    for path in paths:
        raw = git("show", f"{SHARED}:{path}")
        target = directory / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        overlay[path] = digest(raw)
    return overlay


def disclosed(directory):
    record = json.loads(checked(directory / "SourceLock.json", LOCK))
    demand(record["passed"] and record["cohort"] == "disclosed"
           and record["oracle_build"] == "34.5.2.0604" and record["oracle_sha256"] == ORACLE
           and record["fresh_processes"] == record["distinct_processes"] == 12
           and record["writer_output_count"] == 0 and record["inputs_unchanged"]
           and record["heldout_writer_acceptance"] is False
           and set(record["controls"]) == {"before", "after"}
           and all(row["passed"] for row in record["controls"].values()),
           "disclosed lock and bracket controls differ")
    prior = git("show", f"{RESEARCH}:re/solidworks/measurements/2026/OrdinarySweepGhostOwnership01.json")
    demand(digest(prior) == PRIOR_REPLAY, "original disclosed ownership replay differs")
    prior_rows = {(row["slot"], row["role"]): row for row in json.loads(prior)["cases"]}
    authored = json.loads(checked(HERE.with_name("DisclosedSweepInputs.json"), record["spec_sha256"]))
    jobs = []
    for slot, (source, model) in enumerate(zip(record["sources"], authored["cases"], strict=True), 1):
        demand(source["slot"] == slot - 1 and source["passed"], "wrong source-lock slot")
        for role, suffix in ROLES:
            previous = prior_rows[slot, role]
            pin = source["artifact_sha256"][role]
            demand(previous["source_sha256"] == pin, "source and original native replay disagree")
            raw = checked(directory / f"{model['name']}{suffix}.SLDPRT", pin)
            section = model["edit_section_radius_m" if role == "section" else "section_radius_m"]
            path = model["edit_path_radius_m" if role == "path" else "path_radius_m"]
            jobs.append({"slot": slot, "role": role, "file_sha256": pin,
                         "payload": b64encode(raw).decode("ascii"), "drivers_m": [2 * section, path],
                         "older_stream_digests": previous["exact_streams"],
                         "native_phase": previous["native_phase"]})
    demand(len(jobs) == 6, "six disclosed saves are required")
    return record, jobs


def supervise(disclosed_root):
    lock, jobs = disclosed(disclosed_root)
    with TemporaryDirectory(prefix="KitScopedSavedSweep") as scratch:
        sdk = Path(scratch)
        overlay = scratch_sdk(sdk)
        states = []
        for job in jobs:
            worker = run((sys.executable, "-I", "-B", str(HERE), "--worker", str(sdk / "src")),
                         input=json.dumps(job), encoding="utf-8", capture_output=True, timeout=45, check=False)
            demand(worker.returncode == 0 and not worker.stderr, worker.stderr or worker.stdout)
            states.append(json.loads(worker.stdout))
    return {
        "schema": "kit.sw2026.scoped-saved-sweep-replay.v1",
        "base": BASE, "base_src": BASE_SRC, "shared": SHARED, "shared_src": SHARED_SRC,
        "shared_archive_files": overlay, "older_replay_revision": RESEARCH,
        "older_replay_sha256": PRIOR_REPLAY, "lock_sha256": LOCK,
        "oracle_build": lock["oracle_build"], "oracle_sha256": ORACLE,
        "native_controls": {key: row["receipt_sha256"] for key, row in lock["controls"].items()},
        "native_launches": 0, "written_archives": 0, "new_heldout_credit": 0,
        "python": sys.version.split()[0], "zlib": ZLIB_RUNTIME_VERSION,
        "fresh_processes": len(states), "exact_streams": sum(len(row["streams"]) for row in states),
        "tool_sha256": {path.name: digest(path.read_bytes()) for path in
                        (HERE, HERE.with_name("SavedSweepReplay.py"), HERE.with_name("SavedSweepOwners.py"))},
        "states": states,
    }


def main():
    parser = ArgumentParser(description="Replay only the six locked disclosed saved sweep archives")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--disclosed", type=Path)
    modes.add_argument("--worker", type=Path)
    request = parser.parse_args()
    if request.worker:
        sys.path[:0] = [str(request.worker), str(HERE.parent)]
        from SavedSweepReplay import inspect

        job = json.load(sys.stdin)
        raw = b64decode(job.pop("payload"), validate=True)
        demand(digest(raw) == job["file_sha256"], "worker did not receive the locked bytes")
        result = inspect(raw, job)
    else:
        result = supervise(request.disclosed)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
