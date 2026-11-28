from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
from subprocess import check_output
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(HERE.parent), str(HERE.parent.parent)]

from ObserveAttachedBoxAxes import CONTROL, NATIVE, ORACLE, SCHEMA, SOURCE, TOOLS
from RunAttachedTopBoxSources import DISCLOSED_EDITS, ORIGINAL_F14C, ORACLE_VERSION


BUILD = "93189f21691fc1cd3ba0f26beb62541f85ac3f814ae68444d178f639099efe60"
CANDIDATE = "0d4cba0b66e443e487793204dc82985d5206704a0646b63afb1a4c410b1c54cc"


def fingerprint(data):
    return sha256(data).hexdigest()


def read_verified(path, checksum):
    data = path.read_bytes()
    if not path.is_file() or path.is_symlink() or fingerprint(data) != checksum:
        raise ValueError(f"attached box input identity changed at {path.name}")
    return data


def frozen_tool(name, revision):
    path = HERE.with_name(name)
    if not path.is_file():
        path = HERE.parent.parent / name
    relative = path.relative_to(ROOT).as_posix()
    staged = check_output(("git", "show", f"{revision}:{relative}"), cwd=ROOT)
    if staged != path.read_bytes():
        raise ValueError(f"observer differs from its committed revision at {name}")
    return staged


def stage(candidate_folder, control_path, output):
    report_bytes = read_verified(candidate_folder / "Build.json", BUILD)
    report = loads(report_bytes)
    payload = read_verified(candidate_folder / NATIVE.name, CANDIDATE)
    control = read_verified(control_path, CONTROL)
    if (
        report["schema"] != "kit.sw2026.attached-box-xyz-candidate.v1"
        or report["candidate"]["sha256"] != CANDIDATE
        or report["candidate"]["bytes"] != len(payload)
        or report["source_sha256"] != SOURCE
        or report["exact_guest_locator"] != str(NATIVE)
        or tuple(report["expected"]["dimensions_m"]) != ORIGINAL_F14C
        or report["runtime_input_file_reads"] != 0
        or report["native_processes_started"] != 0
        or report["native_acceptance"] is not False
        or report["passed"] is not True
    ):
        raise ValueError("the packet does not bind the exact model-only axes candidate")
    if output.exists() or output.is_relative_to(ROOT):
        raise ValueError("use a fresh host output folder outside the repository")
    revision = check_output(("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()
    tools = {name: frozen_tool(name, revision) for name in sorted(TOOLS)}
    job = {
        "schema": SCHEMA,
        "native_path": str(NATIVE),
        "oracle_sha256": ORACLE,
        "oracle_version": ORACLE_VERSION,
        "control_sha256": CONTROL,
        "source_sha256": SOURCE,
        "candidate_sha256": CANDIDATE,
        "build_sha256": BUILD,
        "observer_revision": revision,
        "source_text": report["source_text"],
        "original_m": ORIGINAL_F14C,
        "edit_m": DISCLOSED_EDITS,
        "tools": {name: fingerprint(data) for name, data in tools.items()},
    }
    output.mkdir()
    (output / "Tools").mkdir()
    for name, data in tools.items():
        (output / "Tools" / name).write_bytes(data)
    for name, data in ((NATIVE.name, payload), ("Control.SLDPRT", control), ("Build.json", report_bytes)):
        (output / name).write_bytes(data)
    raw_job = (dumps(job, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    (output / "Job.json").write_bytes(raw_job)
    return {"job_sha256": fingerprint(raw_job), "file_count": len(tools) + 4,
            "native_launcher_runs": 0, "candidate_sha256": CANDIDATE}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(dumps(stage(args.candidate.resolve(), args.control.resolve(), args.output.resolve())))
