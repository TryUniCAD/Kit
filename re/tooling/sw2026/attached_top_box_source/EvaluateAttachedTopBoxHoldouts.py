from argparse import ArgumentParser
from base64 import b64decode
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
import json
import os
from pathlib import Path, PureWindowsPath
import re
from shutil import copyfile
from subprocess import check_output, run
from sys import executable
from zipfile import ZipFile

from AuthorCurves import digest, require, write_json
from AuthorRectangleAnchors import CONTROL, ORACLE, control
from RunAttachedTopBoxSources import ORACLE_VERSION, TOOLS as SOURCE_TOOLS, unchanged, phase


SCHEMA = "kit.sw2026.attached-top-box-heldout-evaluation.v1"
WRITER_REVISION = "46f2463dfae91263143b24fb98531e610d929f63"
SOURCE_OWNER = "6aaa7af77c7fa3573c2884c80da32dc4aa072be8"
TOOLS = {*SOURCE_TOOLS, "EvaluateAttachedTopBoxHoldouts.py"}
SLOTS = ("Slot01", "Slot02")


def prepare(args):
    command_root = Path(__file__).resolve().parents[4]
    script_path = Path("re/tooling/sw2026/attached_top_box_source")
    require(re.fullmatch(r"[a-f0-9]{40}", args.revision), "use the committed projector revision")
    require(digest(args.control) == CONTROL, "use the pristine rectangle control")
    target = PureWindowsPath(args.target)
    require(target.is_absolute() and target.drive.casefold() == "c:" and len(target.parts) == 2
            and re.fullmatch(r"KitAttachedTopBoxHoldouts[0-9]{2}", target.name),
            "use a previously unused Windows-local evaluation root")
    run(["git", "-C", str(command_root), "merge-base", "--is-ancestor", SOURCE_OWNER, WRITER_REVISION], check=True)

    def blob(path):
        return check_output(["git", "-C", str(command_root), "show", args.revision + ":" + Path(path).as_posix()])

    packet = args.packet.resolve()
    packet.mkdir()
    (packet / "Tools").mkdir()
    for name in TOOLS:
        path = script_path / name if (command_root / script_path / name).is_file() else script_path.parent / name
        (packet / "Tools" / name).write_bytes(blob(path))
    copyfile(args.control, packet / "Control.SLDPRT")
    lock = "re/solidworks/measurements/2026/AttachedTopBoxSourcesNative01.json"
    (packet / "SourceLock.json").write_bytes(blob(lock))
    guard_paths = (
        "tests/__init__.py", "tests/Convert/__init__.py", "tests/Convert/Solidworks/__init__.py",
        "tests/Convert/Solidworks/Research/ConstructionGuard.py",
    )
    for label, revision, extra, entry in (
        ("Projector", args.revision, (), "ProjectNativeAttachedTopBox.py"),
        ("Writer", WRITER_REVISION, guard_paths, "EmitNativeAttachedTopBox.py"),
    ):
        path = packet / (label + ".zip")
        path.write_bytes(check_output(["git", "-C", str(command_root), "archive", "--format=zip", revision, "src", *extra]))
        with ZipFile(path, "a") as archive:
            archive.writestr((script_path / entry).as_posix(), blob(script_path / entry))
    job = packet / "Job.json"
    write_json(job, {
        "schema": SCHEMA, "writer_revision": WRITER_REVISION, "projector_revision": args.revision,
        "oracle_sha256": ORACLE, "oracle_file_version": ORACLE_VERSION, "control_sha256": CONTROL,
        "target": str(target), "creation_epoch": args.creation_epoch,
        "inputs": {name: digest(packet / name) for name in ("SourceLock.json", "Writer.zip", "Projector.zip")},
        "tools": {name: digest(packet / "Tools" / name) for name in TOOLS},
    })
    print(json.dumps({"job_sha256": digest(job), "writer_revision": WRITER_REVISION,
                      "projector_revision": args.revision}))


def checked(root, name, checksum):
    path = (root / name).resolve(strict=True)
    require(path.is_relative_to(root) and path.is_file() and digest(path) == checksum,
            "frozen held-out packet identity changed")
    return path


def read_job(path, checksum):
    root = path.parent
    job = json.loads(checked(root, path.name, checksum).read_bytes())
    require(job["schema"] == SCHEMA and job["writer_revision"] == WRITER_REVISION
            and re.fullmatch(r"[a-f0-9]{40}", job["projector_revision"])
            and job["oracle_sha256"] == ORACLE and job["oracle_file_version"] == ORACLE_VERSION
            and job["control_sha256"] == CONTROL and set(job["tools"]) == TOOLS
            and Path(__file__).resolve().parent == root / "Tools",
            "held-out evaluation must use the frozen writer, projector and oracle")
    for name, expected in job["tools"].items():
        checked(root / "Tools", name, expected)
    for name in ("SourceLock.json", "Writer.zip", "Projector.zip"):
        checked(root, name, job["inputs"][name])
    checked(root, "Control.SLDPRT", CONTROL)
    target = PureWindowsPath(job["target"])
    require(target.is_absolute() and target.drive.casefold() == "c:" and len(target.parts) == 2
            and re.fullmatch(r"KitAttachedTopBoxHoldouts[0-9]{2}", target.name),
            "use a previously unused Windows-local evaluation root")
    require(type(job["creation_epoch"]) is int and job["creation_epoch"] > 0,
            "the candidate file needs a declared creation time")
    return job


def unpack(source, target):
    target.mkdir()
    with ZipFile(source) as archive:
        for member in archive.infolist():
            local = target / member.filename
            require(local.resolve().is_relative_to(target.resolve()), "unsafe frozen source archive path")
        archive.extractall(target)


def source_data(packet):
    lock = json.loads((packet / "SourceLock.json").read_bytes())
    sealed = lock["packets"]["sealed"]
    require(sealed["passed"] and sealed["controls_healthy"]
            and sealed["source_revision"] == SOURCE_OWNER
            and lock["heldout_sources_locked_before_writer"] == 2
            and lock["heldout_payloads_shared"] == 0 and set(sealed["sources"]) == set(SLOTS),
            "the original source locks are incomplete")
    root = Path(r"C:\KitAttachedTopBoxSources02")
    spec = root / "SourceSpecifications.json"
    require(digest(spec) == sealed["spec_sha256"], "guest-private source specification changed")
    specifications = json.loads(spec.read_bytes())
    require(set(specifications) == set(SLOTS), "guest-private held-out roles differ")
    for name in SLOTS:
        unchanged(root / name, sealed["sources"][name]["files"])
    return root, sealed["sources"], specifications


def emit(projector, writer, source, expected, target, creation):
    scripts = Path("re/tooling/sw2026/attached_top_box_source")
    projected = run(
        [executable, "-B", str(projector / scripts / "ProjectNativeAttachedTopBox.py"),
         str(source), expected, "--native-path", str(target), "--creation-epoch", str(creation)],
        capture_output=True, check=True,
    )
    request = projected.stdout
    require(set(json.loads(request)) == {"document", "native_path", "creation_epoch"},
            "the projector must send only its declared neutral request")
    outputs = [
        run([executable, "-I", "-B", str(writer / scripts / "EmitNativeAttachedTopBox.py")],
            input=request, capture_output=True, check=True).stdout
        for _ in range(2)
    ]
    require(outputs[0] == outputs[1], "different guarded builds of the same input")
    report = json.loads(outputs[0])
    content = b64decode(report.pop("blob"), validate=True)
    require(report["passed"] and report["runtime_input_file_reads"] == 0
            and report["bytes"] == len(content) and report["sha256"] == sha256(content).hexdigest(),
            "the held-out candidate does not match its guarded build")
    with target.open("xb") as file:
        file.write(content)
    return report | {"neutral_sha256": sha256(request).hexdigest(), "guarded_builds": 2}


def evaluate(job_path, expected):
    require(os.name == "nt", "native held-out evaluation runs in the Windows guest")
    job = read_job(job_path, expected)
    packet = job_path.parent
    source, source_files, cases = source_data(packet)
    root = Path(job["target"])
    root.mkdir()
    public = packet / "Result.json"
    require(not public.exists(), "the held-out result path is already occupied")
    control_path = root / "Control.SLDPRT"
    copyfile(packet / control_path.name, control_path)
    require(digest(control_path) == CONTROL, "guest-local control differs")
    projector, writer = root / "Projector", root / "Writer"
    unpack(packet / "Projector.zip", projector)
    unpack(packet / "Writer.zip", writer)
    status = {
        "schema": SCHEMA, "stage": "setup", "job_sha256": expected, "passed": False,
        "writer_revision": WRITER_REVISION, "projector_revision": job["projector_revision"],
        "source_lock_sha256": job["inputs"]["SourceLock.json"], "oracle_sha256": ORACLE,
        "oracle_file_version": ORACLE_VERSION, "phases": [], "cases": {},
        "heldout_payloads_shared": 0, "benchmark_conversion_credits": 0,
    }
    write_json(public, status)

    def measure(label, operation, *args, **kwargs):
        status["stage"] = label
        write_json(public, status)
        result = operation(*args, **kwargs)
        identity = result.get("oracle_identity") or {}
        status["phases"].append({
            "name": label, "passed": result["passed"], "record_sha256": result["record_sha256"],
            "process_id": identity.get("process_id"), "process_birth": identity.get("process_creation_filetime"),
            "numeric_checks": result.get("numeric_checks"),
        })
        write_json(public, status)
        require(result["passed"] and identity.get("sha256") == ORACLE,
                "the native held-out phase did not pass on the exact oracle")
        return result

    with (root / "Oracle.log").open("x", encoding="utf-8") as log, redirect_stdout(log), redirect_stderr(log):
        try:
            measure("ControlBefore", control, root, "ControlBefore", control_path)
            for name in SLOTS:
                item = root / name
                item.mkdir()
                status["stage"] = name + "GuardedBuild"
                write_json(public, status)
                original = source / name / "Native" / "Original.SLDPRT"
                locked = source_files[name]["files"]["Original"]["sha256"]
                output = item / "SignedBox.SLDPRT"
                build = emit(projector, writer, original, locked, output, job["creation_epoch"])
                edited = measure(name + "Edit", phase, item, cases[name], "Author", generated_input=output)
                reopened = measure(name + "Reopen", phase, item, cases[name], "Reopen", edited)
                unchanged(source / name, source_files[name]["files"])
                require(digest(output) == build["sha256"], "the generated original was mutated")
                status["cases"][name] = {
                    "original_source_sha256": locked, "build": build, "native_saves": reopened["files"],
                }
                write_json(public, status)
        except Exception as error:
            status["failure"] = {"stage": status["stage"], "type": type(error).__name__}
            print(repr(error))
            if hasattr(error, "stderr") and error.stderr is not None:
                print(error.stderr.decode(errors="replace"))
        finally:
            try:
                measure("ControlAfter", control, root, "ControlAfter", control_path)
            except Exception as error:
                status["control_failure"] = type(error).__name__
                print(repr(error))
    read_job(job_path, expected)
    source_data(packet)
    identities = {(row["process_id"], row["process_birth"]) for row in status["phases"] if row["process_id"] is not None}
    status["controls_healthy"] = [row["passed"] for row in status["phases"]
                                  if row["name"] in ("ControlBefore", "ControlAfter")] == [True, True]
    status["distinct_processes"] = len(identities)
    status["passed"] = (len(identities) == len(status["phases"]) == 6 and status["controls_healthy"]
                        and len(status["cases"]) == len(SLOTS) and not ({"failure", "control_failure"} & status.keys()))
    status["heldout_candidates_passed"] = len(SLOTS) if status["passed"] else 0
    status["stage"] = "heldout_batch_passed" if status["passed"] else "heldout_batch_failed"
    write_json(public, status)
    print(json.dumps({key: status[key] for key in ("stage", "controls_healthy", "distinct_processes", "heldout_candidates_passed")}))
    return 0 if status["passed"] else 3


if __name__ == "__main__":
    parser = ArgumentParser(description="Measure frozen generated boxes against original guest-private source locks")
    modes = parser.add_subparsers(dest="mode", required=True)
    host = modes.add_parser("prepare")
    host.add_argument("control", type=Path)
    host.add_argument("packet", type=Path)
    host.add_argument("--revision", required=True)
    host.add_argument("--target", required=True)
    host.add_argument("--creation-epoch", type=int, required=True)
    guest = modes.add_parser("run")
    guest.add_argument("job", type=Path)
    guest.add_argument("sha256")
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args)
        raise SystemExit(0)
    raise SystemExit(evaluate(args.job.resolve(strict=True), args.sha256))
