from base64 import b64decode
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
from stat import S_ISLNK
from subprocess import run
import sys
from zipfile import ZipFile


from SweepColdPacket import API, COMMON_FILES, LOCK
from SweepEvaluationGate import DISCLOSED_JOB, DISCLOSED_RESULT, SDK_TREE, WRITER, prewriter, verified_file
from SweepModel import require
from SweepPacket import BUILD, CONTROL, FAMILY, ORACLE, job_bytes, valid_hash, windows_paths


METHOD_SCHEMA = "kit.sw2026.standard-sweep-heldout-method.v1"
METHOD = "Method.json"
EVALUATOR = ("SweepEvaluationGate.py", "SweepEvaluationPacket.py", "EvaluateSweepHeldout.py")
PRODUCER = f"{FAMILY}/SweepHoldoutProducer.py"
METHOD_FILES = COMMON_FILES - {"Spec.json", "Predictions.json"} | {
    *(f"Tool/{name}" for name in EVALUATOR), "SourceLock.json", "Writer.zip", "DisclosedResult.json",
}
REQUIRED_NATIVE_PARITY = ("SweepArcNear", "SweepArcWide")


def read_method(path, pin):
    require(path.name == METHOD, "unrecognized sweep evaluation method filename")
    job = json.loads(verified_file(path, pin))
    require(job["schema"] == METHOD_SCHEMA and (job["oracle_build"], job["oracle_sha256"]) == (BUILD, ORACLE)
            and (job["disclosed_job_sha256"], job["writer_revision"], job["sdk_tree"], job["prewriter_lock_sha256"])
            == (DISCLOSED_JOB, WRITER, SDK_TREE, LOCK) and valid_hash(job["method_revision"], 40)
            and job["disclosed_result_sha256"] == DISCLOSED_RESULT and job["parity"] == list(REQUIRED_NATIVE_PARITY)
            and isinstance(job["writer_research"], list) and PRODUCER in job["writer_research"],
            "sweep method is outside its exact pre-writer and disclosed native evidence")
    root = path.parent
    require(set(job["files"]) == METHOD_FILES and {item.relative_to(root).as_posix() for item in root.rglob("*")
            if item.is_file()} == METHOD_FILES | {METHOD}, "sweep method inventory differs")
    pins = {"SourceLock.json": LOCK, "ExpectedApi.json": API, "Control.SLDPRT": CONTROL,
            "DisclosedResult.json": job["disclosed_result_sha256"]}
    for name, evidence in job["files"].items():
        item = root / name
        require(item.stat().st_size == evidence["bytes"] and evidence["sha256"] == pins.get(name, evidence["sha256"]),
                "sweep method member has the wrong declared size or digest")
        verified_file(item, evidence["sha256"])
    result = json.loads((root / "DisclosedResult.json").read_bytes())
    require(result["passed"] is True and result["job_sha256"] == DISCLOSED_JOB,
            "protected method requires the passing disclosed 02 receipt")
    guest_base(job)
    return job, prewriter((root / "SourceLock.json").read_bytes())


def guest_base(job):
    root = PureWindowsPath(job["guest_root"])
    windows_paths(str(root / "Packet"), str(root / "Records"), job["guest_checkout"])
    checkout = PureWindowsPath(job["guest_checkout"])
    require(not root.is_relative_to(checkout) and not checkout.is_relative_to(root) and len(root.parts) > 1,
            "guest evaluation root overlaps checkout or the drive itself")
    return root


def write_files(root, files):
    require(root.is_absolute() and not root.exists(), "sweep method requires a new absolute directory")
    root.mkdir(parents=True, exist_ok=False)
    for name, raw in sorted(files.items()):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(raw)


def inventory(files):
    return {name: {"bytes": len(raw), "sha256": sha256(raw).hexdigest()} for name, raw in files.items()}


def extract_writer(raw, root, sources):
    seen = set()
    research = set()
    with ZipFile(BytesIO(raw)) as archive:
        for entry in archive.infolist():
            path = PurePosixPath(entry.filename)
            require(not path.is_absolute() and ".." not in path.parts and "\\" not in entry.filename
                    and ":" not in entry.filename and not S_ISLNK(entry.external_attr >> 16)
                    and entry.filename.casefold().rstrip("/") not in seen,
                    "writer archive has a noncanonical, duplicate or non-file member")
            seen.add(entry.filename.casefold().rstrip("/"))
            if entry.is_dir():
                continue
            require(path.parts[0] == "src" or (entry.filename in sources and path.suffix == ".py"),
                    "writer archive contains an unexpected research member")
            if path.parts[0] != "src":
                research.add(entry.filename)
            target = root.joinpath(*path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(archive.read(entry))
    require(research == set(sources), "writer research closure differs")


def produce(writer, request):
    child = run((sys.executable, "-I", "-B", str(writer / PRODUCER)), input=job_bytes(request),
                cwd=writer, capture_output=True, timeout=120, check=False)
    require(child.returncode == 0 and not child.stderr, "guarded sweep producer refused the declared model")
    result = json.loads(child.stdout)
    raw = b64decode(result.pop("part"), validate=True)
    require(result == {"candidate_sha256": sha256(raw).hexdigest(), "stream_count": 11,
                       "exact_replays": 3, "blocked_runtime_calls": 0} and raw,
            "guarded sweep producer did not verify its model and output")
    return raw, result


def staged_method(path, pin):
    require(os.name == "nt" and sys.version_info[:2] == (3, 12), "protected evaluation is guest-only CPython 3.12")
    job, lock = read_method(path, pin)
    base = Path(guest_base(job))
    require(base.resolve() == base and path == base / "Method" / METHOD
            and Path(__file__).resolve().parent == path.parent / "Tool", "run from the fresh staged evaluation method")
    return job, lock, base
