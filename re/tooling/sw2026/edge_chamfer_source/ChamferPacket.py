import argparse
import json
import math
import os
import re
import subprocess
from pathlib import Path

from FilletModel import require
from FilletPacket import BUILD, CONTROL, ORACLE, digest, job_bytes, windows_paths

from ChamferModel import predictions, validate_spec

SCHEMA = "kit.sw2026.edge-chamfer-source-job.v1"
RESEARCH = "re/tooling/sw2026"
FAMILY = f"{RESEARCH}/edge_chamfer_source"
TOOLS = {
    FAMILY: ("ChamferApi.py", "ChamferAuthor.py", "ChamferModel.py", "ChamferPacket.py",
             "RunChamferSources.py", "SealChamferSources.py"),
    f"{RESEARCH}/edge_fillet_source": ("FilletApi.py", "FilletAuthor.py", "FilletModel.py", "FilletPacket.py",
                                       "FilletSourcePhase.py"),
    RESEARCH: ("AuthorCurves.py", "AuthorBlindCutSources.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py"),
}
TOOL_FILES = {f"Tool/{name}" for names in TOOLS.values() for name in names}
FILES = TOOL_FILES | {"Control.SLDPRT", "Spec.json", "Predictions.json"}


def write_new(path, value):
    with path.open("xb") as stream:
        stream.write(job_bytes(value))


def valid_hash(value, width=64):
    return isinstance(value, str) and re.fullmatch(f"[0-9a-f]{{{width}}}", value) is not None


def predictions_match(frozen, computed):
    if type(frozen) is not type(computed):
        return False
    if isinstance(computed, float):
        return math.isclose(frozen, computed, rel_tol=1e-13, abs_tol=1e-18)
    if isinstance(computed, list):
        return len(frozen) == len(computed) and all(predictions_match(a, b) for a, b in zip(frozen, computed, strict=True))
    if isinstance(computed, dict):
        return frozen.keys() == computed.keys() and all(predictions_match(frozen[key], value) for key, value in computed.items())
    return frozen == computed


def verify(path, pin, *, private=False):
    if private:
        require(os.name == "nt" and path.resolve().drive.casefold() == "c:", "private source inputs stay on guest C:")
    require(path.name == "SourceJob.json" and path.is_file() and not path.is_symlink()
            and valid_hash(pin) and digest(path) == pin, "unbound source job")
    job = json.loads(path.read_bytes())
    require(job["schema"] == SCHEMA and job["oracle_build"] == BUILD and job["oracle_sha256"] == ORACLE
            and valid_hash(job["source_revision"], 40) and valid_hash(job["source_tree"], 40)
            and job["control_sha256"] == CONTROL and job["writer_output_count"] == 0
            and job["cohort"] in (("disclosed", "heldout") if private else ("disclosed",)), "unbound source policy")
    packet, _, _ = windows_paths(job["guest_packet"], job["guest_capture"], job["guest_checkout"])
    parent = path.parent.resolve()
    if job["cohort"] == "heldout":
        require(parent == Path(packet).resolve() and valid_hash(job["method_job_sha256"])
                and valid_hash(job["disclosed_lock_sha256"]), "unbound protected packet custody")
    require(set(job["files"]) == FILES and job["files"]["Control.SLDPRT"]["sha256"] == CONTROL
            and {item.relative_to(parent).as_posix() for item in parent.rglob("*") if item.is_file()}
            == FILES | {"SourceJob.json"}, "source packet file inventory differs")
    for relative, entry in job["files"].items():
        item = parent / relative
        require(item.is_file() and item.resolve() == item and not item.is_symlink()
                and entry["bytes"] == item.stat().st_size and digest(item) == entry["sha256"],
                f"source packet member differs: {relative}")
    spec = json.loads((parent / "Spec.json").read_bytes())
    cases = validate_spec(spec)
    plans = json.loads((parent / "Predictions.json").read_bytes())
    recomputed = json.loads(job_bytes(predictions(cases)))
    require(spec["cohort"] == job["cohort"] and predictions_match(plans, recomputed), "frozen predictions differ")
    return job, cases, plans


def local_roots(path, job):
    require(os.name == "nt", "source oracle runs only in the root-owned Windows guest")
    packet, capture, checkout = (Path(job[key]).resolve() for key in ("guest_packet", "guest_capture", "guest_checkout"))
    windows_paths(str(packet), str(capture), str(checkout))
    require(path.parent.resolve() == packet and Path(__file__).resolve().parent == packet / "Tool",
            "source phase must run from the verified immutable guest copy")
    return packet, capture


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
    verify(manifest, pin, private=job["cohort"] == "heldout")
    return pin


def stage_guest(path, pin):
    require(os.name == "nt", "guest transfer is Windows-only")
    job, _, _ = verify(path, pin)
    output = Path(job["guest_packet"]).resolve()
    capture = Path(job["guest_capture"]).resolve()
    windows_paths(str(output), str(capture), str(Path(job["guest_checkout"]).resolve()))
    require(not output.exists() and not capture.exists(), "guest experiment packet or capture is already in use")
    data = {name: (path.parent / name).read_bytes() for name in FILES}
    require(create_packet(output, job, data) == pin, "byte-exact packet transfer differs")
    return {"job_sha256": pin, "bound_files": len(data), "native_processes": 0}


def freeze_disclosed(args):
    root = Path(__file__).resolve().parents[4]
    require(valid_hash(args.revision, 40) and not args.output.resolve().is_relative_to(root),
            "use an exact committed revision and a fresh absolute packet outside the repository")

    def git(*arguments):
        return subprocess.check_output(("git", "-C", str(root), *arguments))

    require(git("rev-parse", f"{args.revision}^{{commit}}").decode().strip() == args.revision, "missing exact source commit")
    packet, capture, checkout = windows_paths(args.guest_packet, args.guest_capture, args.guest_checkout)
    data = {f"Tool/{name}": git("show", f"{args.revision}:{parent}/{name}")
            for parent, names in TOOLS.items() for name in names}
    require(args.control.is_file() and digest(args.control) == CONTROL, "disclosed native control differs")
    data["Control.SLDPRT"] = args.control.read_bytes()
    data["Spec.json"] = git("show", f"{args.revision}:{FAMILY}/DisclosedChamferInputs.json")
    data["Predictions.json"] = job_bytes(predictions(validate_spec(json.loads(data["Spec.json"]))))
    job = {"schema": SCHEMA, "cohort": "disclosed", "source_revision": args.revision,
           "source_tree": git("rev-parse", f"{args.revision}^{{tree}}").decode().strip(),
           "oracle_build": BUILD, "oracle_sha256": ORACLE, "control_sha256": CONTROL, "writer_output_count": 0,
           "guest_packet": packet, "guest_capture": capture, "guest_checkout": checkout}
    pin = create_packet(args.output, job, data)
    return {"job_sha256": pin, "prediction_sha256": job["files"]["Predictions.json"]["sha256"],
            "spec_sha256": job["files"]["Spec.json"]["sha256"], "bound_files": len(data), "native_processes": 0}


def main():
    parser = argparse.ArgumentParser(description="Freeze the disclosed native chamfer source method without CAD")
    parser.add_argument("--revision", required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--guest-packet", required=True)
    parser.add_argument("--guest-capture", required=True)
    parser.add_argument("--guest-checkout", required=True)
    print(json.dumps(freeze_disclosed(parser.parse_args()), allow_nan=False))


if __name__ == "__main__":
    main()
