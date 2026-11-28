import hashlib
import json
from pathlib import Path, PureWindowsPath

from FilletModel import require, validate_cases
from FilletPacket import BUILD, CONTROL, FILES, ORACLE, digest, job_bytes

CASE = "EdgeFilletAxial"
SOURCE = r"C:\KitEdgeFilletSource03\Capture\EdgeFilletAxial\EdgeFilletAxial.SLDPRT"
BACKUP = "EdgeFilletAxial.SLDPRT.fillet-cold-probe01.bak"
SOURCE_HASH = "528e0415421149b750a223d3aebdc8e9600f75da8381d9452a22255cd9d993e6"
SOURCE_LOCK = "1f2652129840582cb663063b08f590dadbaf8dd046f0b96f5a1b99cf5ae47797"
SOURCE_JOB = "e37e868be9a2b394c296b30c08a586f5dd5cced5309c2f23503f2b8ba0532c01"
SOURCE_PHASE = "721a5c15e0df77b8467c7a86d4d46439aa50f9a93618292faa37e9da1aa972f5"
REGISTERED_API = "f8bc14e15ee1607deda2a3a2b76e33d7448ed522232e53268286b4da6a25e6d4"
PARTITION = "Contents/Config-0-Partition"
ARMS = ("Intact", "OmitPartition")
TOOL_FILES = {"Tool/FilletColdPacket.py", "Tool/ProbeFilletCold.py"}
NEW_FILES = TOOL_FILES | {"Expected.json", *(f"{arm}.SLDPRT" for arm in ARMS)}
PRIOR_FILES = FILES - {"Tool/AuthorEdgeFillets.py"}
GUEST_ROOT = PureWindowsPath(r"C:\KitEdgeFilletColdProbe01")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(path, pin):
    require(path.is_file() and not path.is_symlink(), "expected an ordinary pinned research file")
    raw = path.read_bytes()
    require(sha(raw) == pin, f"research input hash differs: {path.name}")
    return raw


def write_new(path, value):
    with path.open("xb") as stream:
        stream.write(value)


def read_job(job_path, pin):
    require(job_path.name == "ColdJob.json", "unexpected cold job name")
    job = json.loads(checked(job_path, pin))
    require(job["schema"] == "kit.sw2026.edge-fillet-cold-diagnostic.v1"
            and job["oracle"] == {"build": BUILD, "sha256": ORACLE, "registered_api_sha256": REGISTERED_API}
            and job["source"] == {"file_sha256": SOURCE_HASH, "job_sha256": SOURCE_JOB, "lock_sha256": SOURCE_LOCK,
                                  "phase_sha256": SOURCE_PHASE, "guest_path": SOURCE}
            and job["guest_packet"] == str(GUEST_ROOT / "Packet")
            and job["guest_run"] == str(GUEST_ROOT / "Run01")
            and job["mutation"] == {"action": "omit_one_logical_stream", "stream": PARTITION}
            and job["scope"] == "disclosed native-source diagnostic only"
            and job["writer_output_count"] == 0,
            "cold packet policy differs")
    folder = job_path.parent.resolve()
    file_names = set(job["files"])
    require(file_names == PRIOR_FILES | NEW_FILES
            and file_names | {job_path.name} == {path.relative_to(folder).as_posix()
                                                 for path in folder.rglob("*") if path.is_file()}
            and job["files"]["Control.SLDPRT"]["sha256"] == CONTROL,
            "immutable trial file inventory differs")
    for name, entry in job["files"].items():
        path = folder / name
        require(path.resolve() == path, "trial packet file path is indirect")
        raw = checked(path, entry["sha256"])
        require(len(raw) == entry["bytes"], f"trial packet file size differs: {name}")
    return job


def trial_case(packet):
    spec = json.loads((packet / "Spec.json").read_bytes())
    case, = (case for case in validate_cases(spec) if case["name"] == CASE)
    return case
