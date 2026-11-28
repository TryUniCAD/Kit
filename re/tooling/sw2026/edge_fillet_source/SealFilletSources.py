from argparse import ArgumentParser
from hashlib import sha256 as sha256_bytes
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from AuthorEdgeFillets import write_new
from FilletModel import require, validate_cases
from FilletPacket import BUILD, CONTROL, METHOD_TOOL, ORACLE, digest, inspect_packet, windows_paths

DISCLOSED_JOB = "e37e868be9a2b394c296b30c08a586f5dd5cced5309c2f23503f2b8ba0532c01"
DISCLOSED_LOCK = "1f2652129840582cb663063b08f590dadbaf8dd046f0b96f5a1b99cf5ae47797"
REGISTRATION = "f8bc14e15ee1607deda2a3a2b76e33d7448ed522232e53268286b4da6a25e6d4"
PHASE_TOOLS = ("FilletApi.py", "FilletAuthor.py", "FilletSourcePhase.py",
               "AuthorCurves.py", "AuthorBlindCutSources.py", "OracleIdentity.py", "InspectFresh.py", "Swapp.py")


def digest_bytes(value):
    return sha256_bytes(value).hexdigest()


def pinned_json(path, sha256):
    data = path.read_bytes()
    require(re.fullmatch("[0-9a-f]{64}", sha256) and digest_bytes(data) == sha256, "input SHA-256 differs")
    return json.loads(data)


def validate_completed_lock(lock, cohort):
    require(lock["schema"] == "kit.sw2026.edge-fillet-source-lock.v1" and lock["cohort"] == cohort
            and lock["oracle_build"] == BUILD and lock["oracle_sha256"] == ORACLE
            and lock["registered_api_sha256"] == REGISTRATION and lock["control_sha256"] == CONTROL
            and lock["passed"] is lock["idle_after"] is lock["inputs_unchanged"] is True
            and lock["source_writer_implemented"] is lock["heldout_writer_acceptance"] is False
            and lock["writer_output_count"] == 0 and lock["distinct_processes"] == lock["fresh_processes"] == 8
            and set(lock["controls"]) == {"before", "after"}
            and all(row["passed"] is True and row["receipt_sha256"] for row in lock["controls"].values())
            and len(lock["sources"]) == 2 and all(row["passed"] is True for row in lock["sources"]),
            "source acquisition or immutable native controls did not pass")


def check_prior(prior_job_path, prior_lock_path, method):
    job = pinned_json(prior_job_path, DISCLOSED_JOB)
    lock = pinned_json(prior_lock_path, DISCLOSED_LOCK)
    validate_completed_lock(lock, "disclosed")
    require(job["cohort"] == "disclosed" and lock["job_sha256"] == DISCLOSED_JOB
            and lock["source_revision"] == job["source_revision"] and lock["source_tree"] == job["source_tree"]
            and lock["spec_sha256"] == job["files"]["Spec.json"]["sha256"]
            and all(job["files"][name] == method["files"][name]
                    for name in ("Control.SLDPRT", "Spec.json", *(f"Tool/{tool}" for tool in PHASE_TOOLS))),
            "method must reuse the exact passing native phase tools, control and disclosed intent")


def separate_paths(args, method):
    protected, spec, run, output = (getattr(args, name).resolve() for name in
                                    ("private_root", "spec", "run_root", "publish"))
    method_root = args.method_job.parent.resolve()
    require(all(path.drive.casefold() == "c:" and path.is_absolute()
                for path in (protected, spec, run, output, method_root))
            and protected.parent != protected and protected.is_dir()
            and spec.is_relative_to(protected) and spec.is_file()
            and run.is_relative_to(protected) and not run.exists() and not spec.is_relative_to(run)
            and not output.is_relative_to(protected) and not protected.is_relative_to(output.parent)
            and not output.is_relative_to(method_root) and not method_root.is_relative_to(protected)
            and not protected.is_relative_to(method_root) and output.parent.is_dir() and not output.exists(),
            "expected fresh disjoint local paths for private intent, native capture and digest publication")
    windows_paths(str(run / "Packet"), str(run / "Capture"), method["guest_checkout"])
    return spec, run, output


def validate_independence(private_cases, public_cases):
    require([case["name"] for case in private_cases] == ["Slot01", "Slot02"], "expected two ordered private slots")
    public_radii = {case[key] for case in public_cases for key in ("radius_mm", "edit_radius_mm")}
    require(all(case[key] not in public_radii for case in private_cases for key in ("radius_mm", "edit_radius_mm"))
            and all(case["size_mm"] != original["size_mm"] for case in private_cases for original in public_cases),
            "the private pair must use independently chosen stock sizes and radii")


def bind_private_packet(method_path, method_pin, method, spec, spec_pin, run):
    data = spec.read_bytes()
    require(re.fullmatch("[0-9a-f]{64}", spec_pin) and digest_bytes(data) == spec_pin, "private intent fingerprint changed")
    cases = validate_cases(json.loads(data), "heldout")
    validate_independence(cases, validate_cases(json.loads((method_path.parent / "Spec.json").read_bytes())))
    run.mkdir(parents=True, exist_ok=False)
    packet, capture = run / "Packet", run / "Capture"
    (packet / "Tool").mkdir(parents=True)
    for name in method["files"]:
        value = data if name == "Spec.json" else (method_path.parent / name).read_bytes()
        with (packet / name).open("xb") as stream:
            stream.write(value)
    require(digest(packet / "Spec.json") == spec_pin, "frozen private intent fingerprint changed")
    files = method["files"] | {"Spec.json": {"bytes": len(data), "sha256": spec_pin}}
    job = method | {"cohort": "heldout", "guest_packet": str(packet), "guest_capture": str(capture), "files": files,
                    "method_job_sha256": method_pin, "disclosed_lock_sha256": DISCLOSED_LOCK}
    job_path = packet / "SourceJob.json"
    write_new(job_path, job)
    return job_path, digest(job_path), capture


def run_native(job_path, pin, run):
    command = (sys.executable, "-B", str(job_path.parent / "Tool" / "AuthorEdgeFillets.py"),
               "--job", str(job_path), "--job-sha256", pin)
    with (run / "SupervisorStdout.txt").open("xb") as stdout, (run / "SupervisorStderr.txt").open("xb") as stderr:
        child = subprocess.run(command, stdout=stdout, stderr=stderr, check=False)
    require(child.returncode == 0 and not (run / "SupervisorStderr.txt").stat().st_size,
            "protected source supervisor did not complete cleanly")
    return json.loads((run / "SupervisorStdout.txt").read_bytes())


def supervise(args):
    require(os.name == "nt", "protected acquisition is Windows-only")
    method = inspect_packet(args.method_job, args.method_job_sha256)
    require(method["cohort"] == "method" and Path(__file__).resolve() == (args.method_job.parent / METHOD_TOOL).resolve()
            and args.method_job.parent.resolve() == Path(method["guest_packet"]).resolve(),
            "supervisor is outside the frozen method packet")
    check_prior(args.disclosed_job, args.disclosed_lock, method)
    spec, run, publish = separate_paths(args, method)
    job_path, pin, capture = bind_private_packet(args.method_job, args.method_job_sha256, method,
                                                  spec, args.spec_sha256, run)
    result = run_native(job_path, pin, run)
    require(result["passed"] is True and result["source_lock_sha256"] == digest(capture / "SourceLock.json"),
            "protected source acquisition did not pass")
    lock = pinned_json(capture / "SourceLock.json", result["source_lock_sha256"])
    validate_completed_lock(lock, "heldout")
    require(lock["job_sha256"] == pin and lock["spec_sha256"] == digest(spec) == args.spec_sha256
            and lock["source_revision"] == method["source_revision"] and lock["source_tree"] == method["source_tree"]
            and inspect_packet(args.method_job, args.method_job_sha256) == method
            and [row["case"] for row in lock["sources"]] == ["Slot01", "Slot02"],
            "protected acquisition custody changed")
    sources = []
    for row in lock["sources"]:
        name = row["case"]
        original, edited = row["original_sha256"], row["edited_sha256"]
        require(original == digest(capture / name / f"{name}.SLDPRT")
                and edited == digest(capture / name / f"{name}Edited.SLDPRT")
                and original != edited, "protected native source hash mismatch")
        sources.append({"original_sha256": original, "edited_sha256": edited})
    require(len({digest_value for row in sources for digest_value in row.values()}) == 4,
            "the protected source identities are not distinct")
    write_new(publish, {"schema": "kit.sw2026.edge-fillet-prewriter-lock.v1", "cohort": "heldout", "passed": True,
                        "oracle_build": BUILD, "oracle_sha256": ORACLE, "healthy_bracket_controls": True,
                        "distinct_processes": 8, "source_revision": method["source_revision"],
                        "source_tree": method["source_tree"], "method_job_sha256": args.method_job_sha256,
                        "disclosed_lock_sha256": DISCLOSED_LOCK, "source_writer_implemented": False,
                        "writer_output_count": 0, "heldout_writer_acceptance": False, "sources": sources})
    print(json.dumps({"passed": True, "published_lock_sha256": digest(publish), "sources": len(sources)}))
    return 0


def main():
    parser = ArgumentParser(description="lock protected native fillet sources before writer implementation")
    for flag in ("method-job", "disclosed-job", "disclosed-lock", "private-root", "spec", "run-root", "publish"):
        parser.add_argument(f"--{flag}", type=Path, required=True)
    parser.add_argument("--method-job-sha256", required=True)
    parser.add_argument("--spec-sha256", required=True)
    args = parser.parse_args()
    try:
        return supervise(args)
    except Exception:
        print("protected fillet acquisition did not publish a source lock")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
