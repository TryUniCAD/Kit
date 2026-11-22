import argparse
import hashlib
import json
import math
import os
import re
import subprocess
from pathlib import Path, PureWindowsPath

from EllipseModel import CASES, SCHEMA as INTENT, predict, require, validate


SCHEMA = "kit.sw2026.full-ellipse-blind-boss-job.v1"
BUILD = "34.5.2.0604"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
LOCK = "kit.sw2026.full-ellipse-blind-boss-source-lock.v1"
TOOLS_ROOT = "re/tooling/sw2026"
FAMILY = f"{TOOLS_ROOT}/ellipse_source"
TOOLS = {
    FAMILY: ("EllipseModel.py", "EllipsePacket.py", "EllipseAuthor.py", "RunEllipseSources.py"),
    TOOLS_ROOT: ("AuthorCurves.py", "AuthorBlindCutSources.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py"),
    f"{TOOLS_ROOT}/edge_fillet_source": ("FilletApi.py", "FilletAuthor.py", "FilletModel.py"),
    f"{TOOLS_ROOT}/edge_chamfer_source": ("ChamferModel.py",),
}
CONTROLS = {
    "ControlRectangle.SLDPRT": "31f880dd18a009e6e2cdc5c666484d02f50c7b2117f50051e071cad5d9f21b4f",
    "ControlCircle.SLDPRT": "ee3d82b60adef1a7688fd0e6086d797f8c956c41e070670a581ad8669c9c35b7",
}
ASSETS = "re/solidworks/v2026/corpus/curves-discovery"
FILES = {f"Tool/{name}" for names in TOOLS.values() for name in names} | set(CONTROLS) | {"Spec.json", "Predictions.json"}
SHARE = PureWindowsPath(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover")


def valid_hash(value, width=64):
    return type(value) is str and re.fullmatch(f"[0-9a-f]{{{width}}}", value) is not None


def digest(value):
    return hashlib.sha256(value).hexdigest()


def sha(path):
    return digest(path.read_bytes())


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def put(path, data):
    with path.open("xb") as stream:
        stream.write(data)


def pinned_json(path, pin):
    require(valid_hash(pin) and path.is_file() and not path.is_symlink(), "required immutable receipt is missing")
    raw = path.read_bytes()
    require(digest(raw) == pin, "immutable receipt digest changed")
    return json.loads(raw)


def guest_paths(raw):
    root = PureWindowsPath(raw)
    require(root.is_absolute() and root.drive.casefold() == "c:" and len(root.parts) == 2 and ".." not in root.parts
            and re.fullmatch("KitEllipse[A-Za-z0-9]{2,40}", root.name), "source root must be a fresh named guest-local C: directory")
    return root / "Packet", root / "Capture"


def predictions_equal(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, float):
        return math.isclose(left, right, rel_tol=2e-13, abs_tol=1e-18)
    if isinstance(left, list):
        return len(left) == len(right) and all(predictions_equal(a, b) for a, b in zip(left, right, strict=True))
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(predictions_equal(left[key], value) for key, value in right.items())
    return left == right


def verify(path, pin, *, permit_private=False):
    require(not permit_private or os.name == "nt", "protected source authority is guest-only")
    job = pinned_json(path, pin)
    packet, _ = guest_paths(job["guest_root"])
    require(path.name == "SourceJob.json" and job["schema"] == SCHEMA and job["oracle_build"] == BUILD
            and job["oracle_sha256"] == ORACLE and valid_hash(job["revision"], 40) and valid_hash(job["tree"], 40)
            and job["writer_output_count"] == 0, "wrong source-only packet authority")
    if job["cohort"] != "disclosed":
        require(permit_private and os.name == "nt" and job["cohort"] == "heldout"
                and path.resolve().parent == Path(packet).resolve() and valid_hash(job["disclosed_job_sha256"])
                and valid_hash(job["disclosed_lock_sha256"]), "protected source packet must remain in its bound guest custody")
    parent = path.resolve().parent
    require(set(job["files"]) == FILES and all(job["files"][name]["sha256"] == value for name, value in CONTROLS.items())
            and {item.relative_to(parent).as_posix() for item in parent.rglob("*") if item.is_file()} == FILES | {path.name},
            "source packet inventory or controls differ")
    for name, entry in job["files"].items():
        item = parent / name
        require(item.is_file() and not item.is_symlink() and item.resolve() == item and item.stat().st_size == entry["bytes"]
                and sha(item) == entry["sha256"], f"changed source packet member: {name}")
    cases = validate(json.loads((parent / "Spec.json").read_bytes()), job["cohort"])
    plans = json.loads((parent / "Predictions.json").read_bytes())
    require(predictions_equal(plans, [predict(case) for case in cases]), "frozen independent geometry differs")
    return job, cases, plans


def create(packet, job, files):
    require(not packet.exists() and packet.is_absolute() and files.keys() == FILES, "packet destination or closure differs")
    (packet / "Tool").mkdir(parents=True, exist_ok=False)
    for name, raw in sorted(files.items()):
        put(packet / name, raw)
    job = job | {"files": {name: {"bytes": len(raw), "sha256": digest(raw)} for name, raw in files.items()}}
    path = packet / "SourceJob.json"
    put(path, encode(job))
    pin = sha(path)
    verify(path, pin, permit_private=job["cohort"] == "heldout")
    return pin


def model_files(cohort, cases):
    spec = {"schema": INTENT, "cohort": cohort, "cases": list(cases)}
    return {"Spec.json": encode(spec), "Predictions.json": encode([predict(case) for case in validate(spec, cohort)])}


def freeze(revision, output, raw_root):
    repo = Path(__file__).resolve().parents[4]
    require(valid_hash(revision, 40) and not output.resolve().is_relative_to(repo), "freeze requires a committed revision and external packet")
    guest_paths(raw_root)

    def git(*arguments):
        return subprocess.check_output(("git", "-C", str(repo), *arguments))

    require(git("rev-parse", f"{revision}^{{commit}}").decode().strip() == revision, "source revision is unbound")
    files = {f"Tool/{name}": git("show", f"{revision}:{folder}/{name}") for folder, names in TOOLS.items() for name in names}
    files.update({name: git("show", f"{revision}:{ASSETS}/{name}") for name in CONTROLS})
    require(all(digest(files[name]) == value for name, value in CONTROLS.items()), "committed rectangle or circle control differs")
    files.update(model_files("disclosed", CASES))
    job = {"schema": SCHEMA, "cohort": "disclosed", "revision": revision, "writer_output_count": 0,
           "tree": git("rev-parse", f"{revision}^{{tree}}").decode().strip(), "oracle_build": BUILD,
           "oracle_sha256": ORACLE, "guest_root": raw_root}
    pin = create(output, job, files)
    return {"job_sha256": pin, "spec_sha256": digest(files["Spec.json"]), "prediction_sha256": digest(files["Predictions.json"]),
            "bound_files": len(files), "native_processes": 0}


def local_paths(path, job):
    require(os.name == "nt", "source authority is guest-only")
    packet, capture = (Path(item) for item in guest_paths(job["guest_root"]))
    require(packet.resolve() == packet and capture.resolve() == capture and path.resolve().parent == packet
            and Path(__file__).resolve().parent == packet / "Tool", "launch from the verified guest-local tool directory")
    return packet, capture


def stage(path, pin):
    require(os.name == "nt" and PureWindowsPath(path.resolve()).is_relative_to(SHARE), "stage the disclosed packet from the managed share")
    job, _, _ = verify(path, pin)
    packet, _ = (Path(item) for item in guest_paths(job["guest_root"]))
    require(not packet.parent.exists(), "guest source root is already in use")
    copied = create(packet, job, {name: (path.parent / name).read_bytes() for name in FILES})
    require(copied == pin, "byte-exact guest transfer differs")
    return {"job_sha256": copied, "bound_files": len(FILES), "native_processes": 0}


def main():
    parser = argparse.ArgumentParser(description="Freeze the disclosed ellipse source packet without CAD")
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--guest-root", required=True)
    args = parser.parse_args()
    print(json.dumps(freeze(args.revision, args.output, args.guest_root)))


if __name__ == "__main__":
    main()
