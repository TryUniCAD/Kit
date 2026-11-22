import argparse
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

if Path(__file__).resolve().parent.name == "sweep_source":
    root = Path(__file__).resolve().parents[1]
    sys.path.extend((str(root), str(root / "edge_fillet_source"), str(root / "edge_chamfer_source")))

from FilletPacket import BUILD, CONTROL, ORACLE, digest, job_bytes, windows_paths
from SweepModel import predictions, require, validate_spec

JOB_SCHEMA = "kit.sw2026.standard-sweep-source-job.v1"
RESEARCH = "re/tooling/sw2026"
FAMILY = f"{RESEARCH}/sweep_source"
TOOLS = {
    FAMILY: ("SweepModel.py", "SweepApi.py", "SweepSketches.py", "SweepAuthor.py", "SweepPhase.py",
             "SweepPacket.py", "RunSweepSources.py", "SealSweepSources.py"),
    f"{RESEARCH}/edge_fillet_source": ("FilletApi.py", "FilletAuthor.py", "FilletModel.py", "FilletPacket.py",
                                       "FilletSourcePhase.py"),
    f"{RESEARCH}/edge_chamfer_source": ("ChamferModel.py",),
    RESEARCH: ("AuthorCurves.py", "AuthorBlindCutSources.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py", "SelectedBodyMass.py"),
}
TOOL_FILES = {f"Tool/{name}" for names in TOOLS.values() for name in names}
FILES = TOOL_FILES | {"Control.SLDPRT", "Spec.json", "Predictions.json"}


def valid_hash(value, width=64):
    return isinstance(value, str) and re.fullmatch(f"[0-9a-f]{{{width}}}", value) is not None


def write_new(path, value):
    with path.open("xb") as stream:
        stream.write(job_bytes(value))


def predictions_match(actual, expected):
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, float):
        return math.isclose(actual, expected, rel_tol=1e-13, abs_tol=1e-18)
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(predictions_match(a, b) for a, b in zip(actual, expected, strict=True))
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(predictions_match(actual[key], value) for key, value in expected.items())
    return actual == expected


def verify(path, pin, *, permit_private=False):
    require(valid_hash(pin) and path.name == "SourceJob.json" and path.is_file() and not path.is_symlink()
            and digest(path) == pin, "unbound source job")
    job = json.loads(path.read_bytes())
    require(job["cohort"] == "disclosed" or (permit_private and os.name == "nt" and job["cohort"] == "heldout"),
            "protected source verification is allowed only on the guest")
    require(job["schema"] == JOB_SCHEMA and (job["oracle_build"], job["oracle_sha256"], job["control_sha256"])
            == (BUILD, ORACLE, CONTROL) and valid_hash(job["source_revision"], 40) and valid_hash(job["source_tree"], 40)
            and job["writer_output_count"] == 0, "unbound source-only policy")
    packet, _, _ = windows_paths(job["guest_packet"], job["guest_capture"], job["guest_checkout"])
    parent = path.parent.resolve()
    if job["cohort"] == "heldout":
        require(parent == Path(packet).resolve() and parent.drive.casefold() == "c:"
                and valid_hash(job["method_job_sha256"]) and valid_hash(job["disclosed_lock_sha256"]),
                "unbound protected packet custody")
    require(set(job["files"]) == FILES and job["files"]["Control.SLDPRT"]["sha256"] == CONTROL
            and {item.relative_to(parent).as_posix() for item in parent.rglob("*") if item.is_file()}
            == FILES | {"SourceJob.json"}, "source packet file inventory differs")
    for relative, entry in job["files"].items():
        item = parent / relative
        require(item.is_file() and item.resolve() == item and not item.is_symlink() and entry["bytes"] == item.stat().st_size
                and digest(item) == entry["sha256"], f"source packet member differs: {relative}")
    spec = json.loads((parent / "Spec.json").read_bytes())
    plans = json.loads((parent / "Predictions.json").read_bytes())
    require(spec["cohort"] == job["cohort"] and predictions_match(plans, predictions(spec)), "frozen predictions differ")
    return job, spec, plans


def create_packet(output, job, data):
    require(output.is_absolute() and not output.exists() and set(data) == FILES, "packet destination or closure is unbound")
    output.mkdir(parents=True, exist_ok=False)
    (output / "Tool").mkdir()
    for relative, contents in sorted(data.items()):
        with (output / relative).open("xb") as stream:
            stream.write(contents)
    job["files"] = {name: {"bytes": len(contents), "sha256": digest(output / name)} for name, contents in data.items()}
    manifest = output / "SourceJob.json"
    write_new(manifest, job)
    pin = digest(manifest)
    verify(manifest, pin, permit_private=job["cohort"] == "heldout")
    return pin


def local_roots(path, job):
    require(os.name == "nt" and sys.version_info[:2] == (3, 12), "native source runs in the root-owned Windows CPython 3.12")
    packet, capture, checkout = (Path(job[key]).resolve() for key in ("guest_packet", "guest_capture", "guest_checkout"))
    windows_paths(str(packet), str(capture), str(checkout))
    require(path.parent.resolve() == packet and Path(__file__).resolve().parent == packet / "Tool",
            "native source must run from the immutable guest packet")
    return packet, capture


def stage_guest(path, pin):
    require(os.name == "nt" and sys.version_info[:2] == (3, 12), "guest staging requires Windows CPython 3.12")
    job, _, _ = verify(path, pin)
    output, capture = (Path(job[key]).resolve() for key in ("guest_packet", "guest_capture"))
    windows_paths(str(output), str(capture), job["guest_checkout"])
    require(not output.exists() and not capture.exists(), "guest packet or capture already exists")
    data = {name: (path.parent / name).read_bytes() for name in FILES}
    require(create_packet(output, job, data) == pin, "byte-exact guest transfer differs from the frozen packet")
    return {"job_sha256": pin, "bound_files": len(data), "native_processes": 0}


def freeze_disclosed(args):
    root = Path(__file__).resolve().parents[4]
    require(valid_hash(args.revision, 40) and args.output.is_absolute() and not args.output.resolve().is_relative_to(root),
            "use an exact committed revision and unused absolute output outside the checkout")

    def git(*arguments):
        return subprocess.check_output(("git", "-C", str(root), *arguments))

    require(git("rev-parse", f"{args.revision}^{{commit}}").decode().strip() == args.revision, "missing exact source commit")
    packet, capture, checkout = windows_paths(args.guest_packet, args.guest_capture, args.guest_checkout)
    data = {f"Tool/{name}": git("show", f"{args.revision}:{parent}/{name}")
            for parent, names in TOOLS.items() for name in names}
    require(args.control.is_file() and not args.control.is_symlink() and digest(args.control) == CONTROL,
            "disclosed native control differs")
    data["Control.SLDPRT"] = args.control.read_bytes()
    data["Spec.json"] = git("show", f"{args.revision}:{FAMILY}/DisclosedSweepInputs.json")
    spec = json.loads(data["Spec.json"])
    validate_spec(spec)
    data["Predictions.json"] = job_bytes(predictions(spec))
    job = {"schema": JOB_SCHEMA, "cohort": "disclosed", "source_revision": args.revision,
           "source_tree": git("rev-parse", f"{args.revision}^{{tree}}").decode().strip(), "oracle_build": BUILD,
           "oracle_sha256": ORACLE, "control_sha256": CONTROL, "writer_output_count": 0,
           "guest_packet": packet, "guest_capture": capture, "guest_checkout": checkout}
    pin = create_packet(args.output, job, data)
    return {"job_sha256": pin, "prediction_sha256": job["files"]["Predictions.json"]["sha256"],
            "spec_sha256": job["files"]["Spec.json"]["sha256"], "bound_files": len(data), "native_processes": 0}


def main():
    parser = argparse.ArgumentParser(description="Freeze the disclosed sweep source method without launching CAD")
    parser.add_argument("--revision", required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--guest-packet", required=True)
    parser.add_argument("--guest-capture", required=True)
    parser.add_argument("--guest-checkout", required=True)
    print(json.dumps(freeze_disclosed(parser.parse_args()), allow_nan=False))


if __name__ == "__main__":
    main()
