from argparse import ArgumentParser
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
import json
import os
from pathlib import Path, PureWindowsPath
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import time
from traceback import print_exc


HERE = Path(__file__).resolve()
REPO = HERE.parents[4]
RESEARCH = "re/tooling/sw2026"
IMPORT = f"{RESEARCH}/imported_body_source"
TOOL = f"{IMPORT}/{HERE.name}"
LOCK_PATH = "re/solidworks/measurements/2026/ImportedBaseBodySourcesNative01.json"
LOCK_SHA = "d2568776891dec3f5671dc89d9696ae3d4d4005fb22f4dedf500347939f6de2a"
RAW_LOCK_SHA = "1a5a4993881c967682496c90924c262c7954fddd67dd9d1ee3e105186deed281"
SDK_REVISION = "05e3fceb6ad43593435d39cffe309b1cb044fc57"
SOURCE_ROOT = r"C:\KitImportedBodySources04"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"
VERSION = "34.5.2.0604"
SLOTS = ("Slot01", "Slot02")
SCHEMA = "kit.sw2026.rectangular-bare-paired"
EXTRA = (
    "builders", "para",
    *(f"imported_body_source/{name}" for name in (
        HERE.name, "CheckSealedPublicBox.py", "ProjectDisclosedImport.py",
        "BuildLocalBodyKernel.py", "LocalBodyKernel.py",
    )),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(payload):
    return sha256(payload).hexdigest()


def checked(path, identity):
    require(path.is_file() and not path.is_symlink(), "expected a regular locked file")
    payload = path.read_bytes()
    require(digest(payload) == identity, "locked file checksum differs")
    return payload


def publish(path, value):
    payload = value if isinstance(value, bytes) else (
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    with path.open("xb") as stream:
        stream.write(payload)
    return digest(payload)


def contents(code):
    paths = {}
    for path in sorted(code.rglob("*")):
        require(not path.is_symlink(), "code closure contains a symbolic link")
        if path.is_file():
            paths[path.relative_to(code).as_posix()] = digest(path.read_bytes())
    require(len(paths) > 5000 and len({name.casefold() for name in paths}) == len(paths),
            "incomplete or ambiguous Windows code closure")
    return paths


def source_lock(raw):
    lock = json.loads(raw)["packets"]["sealed"]
    require(lock["raw_result_sha256"] == RAW_LOCK_SHA and lock["cohort"] == "sealed"
            and lock["passed"] and lock["controls_healthy"] and lock["distinct_processes"] == 6
            and lock["heldout_sources_locked"] == len(SLOTS) and tuple(lock["sources"]) == SLOTS
            and lock["heldout_payloads_shared"] == lock["writer_outputs"] == 0
            and lock["native_writer_acceptance"] is False
            and lock["oracle_sha256"] == ORACLE and lock["oracle_version"] == VERSION
            and lock["specifications_locked_at_unix_s"] < lock["source_batch_locked_at_unix_s"],
            "the exact pre-writer source lock differs")
    return lock


def profile(guest):
    require(re.fullmatch(r"C:\\KitSdkSealedBox[0-9]{2}", str(guest)),
            "choose a fresh guest-local rectangular packet")
    return {"schema": SCHEMA + "-job.v1", "sdk_revision": SDK_REVISION,
            "guest_root": str(guest), "source_receipt_sha256": LOCK_SHA,
            "control_sha256": CONTROL, "oracle_sha256": ORACLE, "oracle_version": VERSION}


def freeze(args):
    from ObservePublicCyl import tracked_extract

    destination = args.destination.resolve()
    require(not args.destination.is_symlink() and not destination.exists()
            and not destination.is_relative_to(REPO)
            and re.fullmatch(r"[0-9a-f]{40}", args.revision),
            "use a new external host packet and a committed method revision")
    job = profile(args.guest_root)
    receipt = checked(REPO / LOCK_PATH, LOCK_SHA)
    lock = source_lock(receipt)
    seed = checked(args.control, CONTROL)
    for ancestor in (lock["source_revision"], SDK_REVISION):
        subprocess.run(("git", "merge-base", "--is-ancestor", ancestor, args.revision),
                       check=True, cwd=REPO)
    subprocess.run(("git", "diff", "--quiet", SDK_REVISION, args.revision, "--", "src"),
                   check=True, cwd=REPO)
    frozen = int(subprocess.check_output(("git", "show", "-s", "--format=%ct", args.revision), cwd=REPO))
    require(lock["source_batch_locked_at_unix_s"] < frozen, "method must postdate the input lock")
    code = destination / "Kit"
    code.mkdir(parents=True)
    with TemporaryDirectory(prefix="kit-sealed-box-method-") as scratch:
        tracked_extract(args.revision, code, Path(scratch) / "Files.tar", extra=EXTRA)
    for name in (HERE.name, "CheckSealedPublicBox.py"):
        require((code / IMPORT / name).read_bytes() == HERE.with_name(name).read_bytes(),
                "working method differs from the committed revision")
    publish(destination / "SourceLock.json", receipt)
    publish(destination / "Control.SLDPRT", seed)
    inventory = contents(code)
    job.update(method_revision=args.revision, frozen_at_unix_s=time(), file_inventory=inventory)
    return {"job_sha256": publish(destination / "Job.json", job),
            "code_files": len(inventory), "method_revision": args.revision, "native_processes_started": 0}


def verified_job(path, identity):
    require(os.name == "nt" and sys.dont_write_bytecode, "invoke the frozen method in Windows with -B")
    job = json.loads(checked(path, identity))
    packet = path.parent.resolve()
    code = packet / "Kit"
    root = Path(job["guest_root"])
    require(path.name == "Job.json" and HERE == (code / TOOL).resolve()
            and re.fullmatch(r"[0-9a-f]{40}", job["method_revision"])
            and all(job[key] == value for key, value in profile(root).items()),
            "job does not bind this frozen method and guest profile")
    require(contents(code) == job["file_inventory"], "committed code closure changed")
    lock = source_lock(checked(packet / "SourceLock.json", LOCK_SHA))
    require(job["frozen_at_unix_s"] > lock["source_batch_locked_at_unix_s"],
            "the source lock must precede the evaluation")
    seed = checked(packet / "Control.SLDPRT", CONTROL)
    sys.path[:0] = [str(code / name) for name in (IMPORT, RESEARCH, f"{RESEARCH}/serial", "src", "")]
    return packet, job, lock, seed, root


def guest_run(args):
    packet, job, lock, seed, root = verified_job(args.job, args.job_sha256)
    if args.mode == "verify":
        return {"job_sha256": args.job_sha256, "verified": True, "native_processes_started": 0}
    require(not (packet / "Result.json").exists(), "the public comparison receipt already exists")
    if args.mode == "build":
        root.mkdir()
    require(root.resolve() == root and root.is_dir(), "the private output root differs")
    with (root / (args.mode + ".log")).open("x", encoding="utf-8") as log:
        with redirect_stdout(log), redirect_stderr(log):
            try:
                from CheckSealedPublicBox import build, measure

                if args.mode == "build":
                    return build(root, lock, args.job_sha256)
                return measure(packet, root, job, lock, seed, args.job_sha256, args.build_sha256)
            except Exception as error:
                print_exc()
                return {"passed": False, "phase": args.mode, "error_type": type(error).__name__}


def main():
    parser = ArgumentParser(description="Compare previously locked rectangular sources with bare SDK output")
    modes = parser.add_subparsers(dest="mode", required=True)
    prepare = modes.add_parser("freeze")
    prepare.add_argument("destination", type=Path)
    prepare.add_argument("revision")
    prepare.add_argument("control", type=Path)
    prepare.add_argument("guest_root", type=PureWindowsPath)
    for mode in ("verify", "build", "measure"):
        stage = modes.add_parser(mode)
        stage.add_argument("job", type=Path)
        stage.add_argument("job_sha256")
        if mode == "measure":
            stage.add_argument("build_sha256")
    args = parser.parse_args()
    result = freeze(args) if args.mode == "freeze" else guest_run(args)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("passed", True) else 3


if __name__ == "__main__":
    raise SystemExit(main())
