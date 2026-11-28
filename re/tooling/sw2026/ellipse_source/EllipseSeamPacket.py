from argparse import ArgumentParser
import json
import os
from pathlib import Path, PureWindowsPath
import subprocess

from EllipseModel import CASES, predict, require
from EllipsePacket import (ASSETS, BUILD, CONTROLS, FAMILY, ORACLE, SHARE, TOOLS, digest, encode,
                           guest_paths, pinned_json, predictions_equal, put, sha, valid_hash)

SCHEMA = "kit.sw2026.ellipse-seam-discriminator-job.v1"
SOURCE_METHOD = "dfc8e26a9bc58d382f741d00e9e5ee0bd49362b1"
TEMPLATE_SHA256 = "b82f8f25d797f5fc4e110f566c2469d8ec87637fb7b220eae444e4918afefb15"
SOURCE_LOCK = "1ecae416cf69cc532072418ec56a55df62c3abe2e638851ea41777352e736fd5"
LOCK_PATH = "re/solidworks/measurements/2026/EllipseBlindBossDisclosedLock01.json"
JOB = "SeamJob.json"
RESULT = "SeamResult.json"
TOOLS_CLOSURE = TOOLS | {FAMILY: (*TOOLS[FAMILY], "EllipseSeamPacket.py", "EllipseSeamObserve.py",
                                "EllipseSeamAuthor.py", "RunEllipseSeam.py")}
LOCK = "DisclosedSourceLock.json"
FILES = {f"Tool/{name}" for names in TOOLS_CLOSURE.values() for name in names} | set(CONTROLS) | {
    LOCK, "Shape.json", "Prediction.json",
}
DESTINATIONS = {"sketch": "EllipseSketchOnly.SLDPRT", "boss": "EllipseBlindBoss.SLDPRT"}


def verify(path, pin):
    job = pinned_json(path, pin)
    parent = path.resolve().parent
    guest_paths(job["guest_root"])
    require(path.name == JOB and job["schema"] == SCHEMA and job["source_method"] == SOURCE_METHOD
            and job["oracle_build"] == BUILD and job["oracle_sha256"] == ORACLE
            and type(job.get("close_updates", True)) is bool
            and job["writer_output_count"] == 0 and valid_hash(job["host_audit_sha256"]) and valid_hash(job["revision"], 40)
            and valid_hash(job["tree"], 40) and set(job["files"]) == FILES
            and all(job["files"][name]["sha256"] == value for name, value in CONTROLS.items())
            and job["files"][LOCK]["sha256"] == SOURCE_LOCK
            and {item.relative_to(parent).as_posix() for item in parent.rglob("*") if item.is_file()} == FILES | {JOB},
            "ellipse seam packet inventory or authority differs")
    for name, entry in job["files"].items():
        item = parent / name
        require(item.is_file() and item.resolve() == item and not item.is_symlink()
                and item.stat().st_size == entry["bytes"] and sha(item) == entry["sha256"],
                f"ellipse seam packet member changed: {name}")
    prior = pinned_json(parent / LOCK, SOURCE_LOCK)
    require(prior["cohort"] == "disclosed" and prior["passed"]
            and prior["oracle_build"] == BUILD and prior["oracle_sha256"] == ORACLE
            and prior["distinct_processes"] == 10 and prior["writer_output_count"] == 0
            and prior["sources"][0]["original_sha256"] == "27cbc6cb2c5cda422958bad07d40b048450d0bac02e558fb33be10606fe4c5ab",
            "packet did not reuse the disclosed Front A source method")
    shape = json.loads((parent / "Shape.json").read_bytes())
    plan = json.loads((parent / "Prediction.json").read_bytes())
    require(shape == CASES[0] and predictions_equal(plan, predict(shape)),
            "ellipse discriminator intent differs from the independently disclosed source shape")
    return job, plan


def make_packet(output, job, files):
    require(output.is_absolute() and not output.exists() and set(files) == FILES,
            "ellipse seam packet needs a fresh absolute destination and exact closure")
    (output / "Tool").mkdir(parents=True, exist_ok=False)
    for name, data in sorted(files.items()):
        put(output / name, data)
    bound = job | {"files": {name: {"bytes": len(data), "sha256": digest(data)} for name, data in files.items()}}
    path = output / JOB
    put(path, encode(bound))
    pin = sha(path)
    verify(path, pin)
    return pin


def freeze(revision, output, guest_root, *, close_updates=True):
    repo = Path(__file__).resolve().parents[4]
    require(valid_hash(revision, 40) and not output.resolve().is_relative_to(repo),
            "freeze requires a committed revision and external packet")
    guest_paths(guest_root)

    def git(*arguments):
        return subprocess.check_output(("git", "-C", str(repo), *arguments))

    git("merge-base", "--is-ancestor", SOURCE_METHOD, revision)
    require(git("rev-parse", f"{revision}^{{commit}}").decode().strip() == revision,
            "ellipse seam source revision is unbound")
    files = {f"Tool/{name}": git("show", f"{revision}:{folder}/{name}")
             for folder, names in TOOLS_CLOSURE.items() for name in names}
    files |= {name: git("show", f"{revision}:{ASSETS}/{name}") for name in CONTROLS}
    files |= {LOCK: git("show", f"{revision}:{LOCK_PATH}"),
              "Shape.json": encode(CASES[0]), "Prediction.json": encode(predict(CASES[0]))}
    job = {"schema": SCHEMA, "revision": revision, "tree": git("rev-parse", f"{revision}^{{tree}}").decode().strip(),
           "source_method": SOURCE_METHOD, "oracle_build": BUILD, "oracle_sha256": ORACLE,
           "guest_root": guest_root, "close_updates": close_updates, "writer_output_count": 0,
           "host_audit_sha256": digest(git("show", f"{revision}:{FAMILY}/AuditEllipseSeam.py"))}
    pin = make_packet(output, job, files)
    return {"job_sha256": pin, "bound_files": len(FILES), "shape_sha256": digest(files["Shape.json"]),
            "prediction_sha256": digest(files["Prediction.json"]), "native_processes": 0}


def stage(path, pin):
    require(os.name == "nt" and PureWindowsPath(path.resolve()).is_relative_to(SHARE),
            "stage only from the managed disclosed share")
    job, _ = verify(path, pin)
    guest, _ = (Path(value) for value in guest_paths(job["guest_root"]))
    require(not guest.parent.exists(), "guest ellipse seam root is occupied")
    copied = make_packet(guest, job, {name: (path.parent / name).read_bytes() for name in FILES})
    require(copied == pin, "guest ellipse seam staging changed the packet hash")
    return {"job_sha256": pin, "bound_files": len(FILES), "native_processes": 0}


def local_paths(path, job):
    require(os.name == "nt", "ellipse seam oracle authority is guest-only")
    packet, capture = (Path(value) for value in guest_paths(job["guest_root"]))
    require(packet.resolve() == packet and capture.resolve() == capture and path.resolve().parent == packet
            and Path(__file__).resolve().parent == packet / "Tool", "run the verified guest-local ellipse seam packet")
    return packet, capture


if __name__ == "__main__":
    parser = ArgumentParser(description="Freeze an ellipse source seam discriminator without running CAD")
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--guest-root", required=True)
    parser.add_argument("--close-without-update", action="store_true")
    args = parser.parse_args()
    print(json.dumps(freeze(args.revision, args.output, args.guest_root,
                            close_updates=not args.close_without_update), sort_keys=True))
