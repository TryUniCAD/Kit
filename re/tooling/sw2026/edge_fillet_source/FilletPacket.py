import hashlib
import json
import os
import re
from pathlib import Path, PureWindowsPath

from FilletModel import require

SCHEMA = "kit.sw2026.edge-fillet-source-job.v1"
BUILD = "34.5.2.0604"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL = "28e1f9cd045a7a264b2bdf8658ae593744d65ca708def4a48199ec357f063ab0"
SHARED_TOOLS = ("AuthorCurves.py", "AuthorBlindCutSources.py", "OracleIdentity.py", "InspectFresh.py", "Swapp.py")
OWNED_TOOLS = ("AuthorEdgeFillets.py", "FilletApi.py", "FilletAuthor.py", "FilletModel.py", "FilletPacket.py",
               "FilletSourcePhase.py")
METHOD_TOOL = "Tool/SealFilletSources.py"
FILES = frozenset({"Control.SLDPRT", "Spec.json", *(f"Tool/{name}" for name in (*SHARED_TOOLS, *OWNED_TOOLS))})


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def job_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def windows_paths(*args):
    packet, capture, checkout = (PureWindowsPath(value) for value in args)
    require(all(path.is_absolute() and ".." not in path.parts for path in (packet, capture, checkout)),
            "packet, source capture and repository scope require absolute Windows paths")
    require(packet.drive.casefold() == capture.drive.casefold() == "c:"
            and not packet.is_relative_to(capture) and not capture.is_relative_to(packet)
            and not packet.is_relative_to(checkout) and not capture.is_relative_to(checkout)
            and not checkout.is_relative_to(capture) and not checkout.is_relative_to(packet),
            "input packet and source capture must be on disjoint local guest paths outside the checkout")
    return tuple(str(path) for path in (packet, capture, checkout))


def inspect_packet(job_path, expected_hash, *, private=False):
    require(not private or os.name == "nt", "protected packet verification is Windows-only")
    raw = job_path.read_bytes()
    require(re.fullmatch("[0-9a-f]{64}", expected_hash) and hashlib.sha256(raw).hexdigest() == expected_hash,
            "frozen job hash differs")
    job = json.loads(raw)
    cohort = job["cohort"]
    require(cohort in (("disclosed", "heldout") if private else ("disclosed", "method")),
            "the expected packet cohort differs")
    require(job["schema"] == SCHEMA and job["oracle_build"] == BUILD
            and job["oracle_sha256"] == ORACLE and job["control_sha256"] == CONTROL
            and re.fullmatch("[0-9a-f]{40}", job["source_revision"]) and re.fullmatch("[0-9a-f]{40}", job["source_tree"])
            and job["source_writer_implemented"] is False and job["writer_output_count"] == 0,
            "unexpected ordinal or exact source-only job policy")
    windows_paths(job["guest_packet"], job["guest_capture"], job["guest_checkout"])
    parent = job_path.parent.resolve()
    if cohort == "heldout":
        for field in ("method_job_sha256", "disclosed_lock_sha256"):
            require(re.fullmatch("[0-9a-f]{64}", job[field]), "protected source provenance is unbound")
        require(parent == Path(job["guest_packet"]).resolve(), "protected job is outside its frozen local path")
    expected_files = FILES | ({METHOD_TOOL} if cohort in ("method", "heldout") else set())
    require(job_path.name == "SourceJob.json" and set(job["files"]) == expected_files
            and job["files"]["Control.SLDPRT"]["sha256"] == CONTROL,
            "immutable packet file inventory differs")
    require({path.relative_to(parent).as_posix() for path in parent.rglob("*") if path.is_file()}
            == expected_files | {"SourceJob.json"}, "packet contains an unbound file")
    for relative, entry in job["files"].items():
        path = parent / relative
        require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(parent)
                and path.stat().st_size == entry["bytes"] and digest(path) == entry["sha256"],
                f"frozen packet file differs: {relative}")
    return job
