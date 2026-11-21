from argparse import ArgumentParser
from io import BytesIO
import json
import os
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
import sys
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from RunThinHeldout import locked_intents, writer_code
from ThinHeldoutPacket import (
    CASES, LOCK_SHA, ORACLE, PRINCIPAL_JOB, PRINCIPAL_TREE, PRINCIPAL_WRITER, SCHEMA, SPEC, SWROOT, THINROOT,
    VERSION, archive_path, checked, digest, encode, packet_data, publish, require, source_lock,
)
from ThinPublicWrite import NEGATIVES


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
FREEZE = "8c6c5edb5dbd4b8147e77ef3d87ad80982829b431c0d13d0c5c220968e59635a"
GENERATION = "4203f14d32088ad7f8d6a27fe3ea12012688590dff9e68003bd7cdc1f8e2f351"
NATIVE = "ec5eec4fc88ed11cbbd63f90a30cd3e47065393b8c647254dff7a44bde430f13"
PUBLIC = "kit.sw2026.thin-revolve-public-sdk-parity.v1"
WORKER = "ThinPublicWorker.py"
METHODS = (WORKER, "ThinPublicRead.py", "ThinPublicWrite.py")
STANDALONE = ("ProveThinPublic.py", "RunThinHeldout.py", "ThinHeldoutPacket.py", "ThinPublicWrite.py")
BASE = "src/convert/adapters/solidworks/"
THIN_READERS = BASE + "Core/TypedResolved/Revolves/Thin/"
ANNOTATION = BASE + "Archive/Construction/Revolves/Neutral/ReadThinWall.py"
ADMITTED = frozenset(BASE + name for name in (
    "Core/Preparation/PlanNativePart.py",
    "Core/Preparation/PrepareNative.py",
    "Core/Preparation/Revolve/PlanThinPart.py",
    "Core/Adapter.py",
    "Core/TypedResolved/Geometry/ReadNoCache.py",
)) | {ANNOTATION}


def native_result(raw):
    value = json.loads(raw)
    require(digest(raw) == NATIVE and value["schema"] == SCHEMA and value["profile"] == "principal"
            and value["freeze_sha256"] == FREEZE and value["generation_sha256"] == GENERATION
            and value["source_lock_sha256"] == LOCK_SHA and value["writer_revision"] == PRINCIPAL_WRITER
            and value["writer_src_tree"] == PRINCIPAL_TREE and value["oracle_sha256"] == ORACLE
            and value["oracle_build"] == VERSION and value["fresh_processes"] == value["distinct_processes"] == 18
            and value["passed"] and value["heldout_writer_cases_qualified"] == 4 and value["idle_after"]
            and value["control-before"]["passed"] and value["control-after"]["passed"]
            and value["immutable_inputs_reverified"] and value["writer_runtime_external_access_attempts"] == 0
            and value["original_native_files_read_during_generation"] == 0
            and not value["public_writer_qualified"] and not value["whole_source_conversion"]
            and tuple(row["slot"] for row in value["cases"]) == CASES,
            "independent native thin receipt did not qualify the exact four frozen cases")
    require(all(row["passed"] and row["typed_streams"] == 10 and row["repeat_bytes_equal"]
                and row["writer_runtime_external_access_attempts"] == 0
                and all(len(phases) == 2 and all(phase["passed"] and phase["cold_bodies"] == 1
                    and phase["open_status"] == {"opened": True, "errors": 0, "warnings": 0} for phase in phases)
                    for phases in row["native_phases"].values())
                and set(row["comparisons"]) == {"source_to_pre_writer", "candidate_to_current_source"}
                for row in value["cases"]), "native input or derivative scope is incomplete")
    return value


def frozen_source(revision, lock, job):
    from FreezeThinHeldout import git, package

    git("merge-base", "--is-ancestor", PRINCIPAL_WRITER, revision)
    delta = git("diff", "--name-only", PRINCIPAL_WRITER, revision, "--", "src").decode().splitlines()
    require(set(delta) >= ADMITTED and all(path in ADMITTED or path.startswith(THIN_READERS) for path in delta),
            "public variant contains unsupported source or writer changes")
    before, after = (git("show", f"{head}:{ANNOTATION}") for head in (PRINCIPAL_WRITER, revision))
    require(before.replace(b"LengthsValue = []", b"LengthsValue: list[float] = []", 1) == after,
            "writer delta must preserve the measured width calculation")
    pack = BytesIO()
    base = package(lock, job, revision, "principal")
    support = (SWROOT + "VerifySdkCircleEndRegistration.py",
               SWROOT + "revolve/EndModes/ProveTwoDirectionRevolves.py",
               SWROOT + "revolve/PrincipalReader/AuditPrincipalReader.py")
    with ZipFile(BytesIO(base)) as source, ZipFile(pack, "w", compression=ZIP_DEFLATED) as bundle:
        for name in source.namelist():
            bundle.writestr(name, source.read(name))
        for name in (*(THINROOT + tool for tool in METHODS + ("ThinHeldoutPacket.py",)), *support):
            bundle.writestr(archive_path(name).as_posix(), git("show", f"{revision}:{name}"))
    return pack.getvalue(), delta


def freeze(packet, output):
    from FreezeThinHeldout import git

    require(not output.exists() and not output.resolve().is_relative_to(ROOT), "use a fresh external publication packet")
    require(not git("status", "--porcelain", "--untracked-files=no").strip(), "freeze an exact clean public revision")
    measured, lock, _ = packet_data(packet, FREEZE)
    native_raw = checked(packet / "NativeReceipt.json", NATIVE)
    native_result(native_raw)
    job = json.loads(checked(packet / "PrincipalJob.json", PRINCIPAL_JOB))
    revision = git("rev-parse", "HEAD").decode().strip()
    tree = git("rev-parse", "HEAD:src").decode().strip()
    code, delta = frozen_source(revision, lock, job)
    tools = {name: git("show", f"{revision}:{THINROOT}{name}") for name in STANDALONE}
    require(all((HERE / name).read_bytes() == raw for name, raw in tools.items()), "publication supervisor differs from its revision")
    data = {"schema": PUBLIC, "code_sha256": digest(code), "native_sha256": NATIVE, "generation_sha256": GENERATION,
            "source_lock_sha256": LOCK_SHA, "measured_writer": PRINCIPAL_WRITER, "public_revision": revision,
            "public_src_tree": tree, "guest_work": measured["guest_work"], "source_delta": delta,
            "supervisor": {name: digest(raw) for name, raw in tools.items()}, "private_files_read_by_freeze": 0}
    output.mkdir(parents=True)
    files = {"Code.zip": code, "SourceLock.json": checked(packet / "SourceLock.json", LOCK_SHA),
             "NativeReceipt.json": native_raw, **tools}
    for name, raw in files.items():
        publish(output / name, raw)
    return {"freeze_sha256": publish(output / "Manifest.json", encode(data)), "public_revision": revision,
            "public_src_tree": tree, "private_files_read_by_freeze": 0}


def run_worker(code, request):
    tool = code / THINROOT / WORKER
    call = run((sys.executable, "-I", "-B", str(tool)), input=encode(request), capture_output=True, check=False)
    try:
        result = json.loads(call.stdout)
        require(call.returncode == 0 and result.pop("passed") is True and not call.stderr, "public SDK worker refused")
    except (ValueError, KeyError):
        raise ValueError("public SDK worker refused") from None
    return result


def verify(packet, pin):
    require(os.name == "nt" and sys.version_info[:2] == (3, 12), "qualified packet uses Windows Python 3.12 without COM")
    manifest = json.loads(checked(packet / "Manifest.json", pin))
    require(manifest["schema"] == PUBLIC and manifest["native_sha256"] == NATIVE
            and manifest["generation_sha256"] == GENERATION and manifest["source_lock_sha256"] == LOCK_SHA
            and manifest["measured_writer"] == PRINCIPAL_WRITER and manifest["private_files_read_by_freeze"] == 0,
            "public qualification manifest differs from its measured baseline")
    require(set(manifest["supervisor"]) == set(STANDALONE), "publication supervisor closure differs")
    for name, sha in manifest["supervisor"].items():
        require(name in STANDALONE, "unexpected public supervisor file")
        checked(packet / name, sha)
    lock = source_lock(checked(packet / "SourceLock.json", LOCK_SHA))
    measured = native_result(checked(packet / "NativeReceipt.json", NATIVE))
    work = Path(manifest["guest_work"])
    require(PureWindowsPath(work).name == "SdkThinHeldoutEvaluation02", "follow the exact independent guest workspace")
    generation = json.loads(checked(work / "Generation.json", GENERATION))
    require(generation["freeze_sha256"] == FREEZE and generation["writer_revision"] == PRINCIPAL_WRITER
            and generation["writer_src_tree"] == PRINCIPAL_TREE and generation["spec_sha256"] == lock["spec_sha256"]
            and generation["original_native_files_read_during_generation"] == 0
            and generation["writer_runtime_external_access_attempts"] == 0,
            "guest candidate generation provenance differs")
    rows, negatives = {}, {}
    with TemporaryDirectory(dir=work, prefix="SdkPublic-") as temp:
        root = Path(temp)
        code = writer_code(packet, manifest, root, extract=True)
        cases = locked_intents(code, lock)
        for slot, case, result in zip(CASES, cases, measured["cases"], strict=True):
            candidate = work / "Generated" / (case["name"] + ".SLDPRT")
            sha = generation["cases"][slot]["candidate_sha256"]
            require(result["slot"] == slot and result["candidate_sha256"] == sha, "generated slot is not the measured native input")
            require(len(checked(candidate, sha)) == result["candidate_bytes"], "exact archived candidate size differs")
            across = root / slot
            across.mkdir()
            rows[slot] = run_worker(code, {"case": case, "scratch": str(across), "locator": str(candidate),
                                         "epoch": generation["writer_epoch"], "candidate_sha256": sha})
            checked(candidate, sha)
        for label in NEGATIVES:
            lane = root / label
            lane.mkdir()
            negatives[label] = run_worker(code, {"scratch": str(lane), "negative": label})
        code = writer_code(packet, manifest, root, extract=False)
    checked(Path(SPEC), lock["spec_sha256"])
    checked(work / "Generation.json", GENERATION)
    checked(packet / "NativeReceipt.json", NATIVE)
    report = {"schema": PUBLIC, "passed": True, "public_revision": manifest["public_revision"],
              "source_tree": manifest["public_src_tree"], "manifest_sha256": pin, "native_sha256": NATIVE,
              "source_lock_sha256": LOCK_SHA, "generation_sha256": GENERATION, "source_files_read_by_public_qualification": 0,
              "new_native_processes": 0, "whole_source_conversion": False, "cases": rows, "refusals": negatives}
    return {"passed": True, "receipt_sha256": publish(packet / "PublicReceipt.json", encode(report)),
            "public_writer_cases_qualified": len(rows), "refusals": len(negatives)}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("action", choices=("freeze", "verify"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pin")
    args = parser.parse_args()
    try:
        answer = freeze(args.packet, args.output) if args.action == "freeze" else verify(args.packet.resolve(strict=True), args.pin)
    except Exception as error:
        if args.action == "freeze":
            raise
        answer = {"passed": False, "error_type": type(error).__name__}
    print(encode(answer).decode(), end="")
    raise SystemExit(int(answer.get("passed") is False))
