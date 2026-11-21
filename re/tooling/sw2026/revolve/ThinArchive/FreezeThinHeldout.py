from argparse import ArgumentParser
from io import BytesIO
import json
from pathlib import Path
from subprocess import check_output
from tarfile import open as open_tar
from time import time
from zipfile import ZIP_DEFLATED, ZipFile

from ThinHeldoutPacket import (
    DISCLOSURE_JOB_SHA, DISCLOSURE_SHA, LOCK_RELATIVE, LOCK_REVISION, LOCK_SHA, ORACLE,
    PRINCIPAL_BUILD, PRINCIPAL_JOB, SCHEMA, STANDALONE, SWROOT, THINROOT, WRITERS,
    archive_path, checked, digest, disclosure, encode, guest_work, principal_disclosure, publish, require, source_lock,
)


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RESEARCH = (
    *(THINROOT + name for name in ("BuildThinControls.py", "AuditThinArchive.py", "ThinWireOwners.py",
                                  "ThinConstruct.py", "ThinNeutral.py", "CompareThinNative.py", "RunThinNative.py")),
    SWROOT + "revolve/EndModes/AuditRevEndOwners.py",
    SWROOT + "revolve/Preparation/RevolveStreamAudit02.py",
)


def git(*arguments):
    return check_output(("git", *arguments), cwd=ROOT)


def exact_object(revision, path):
    return git("show", f"{revision}:{path}")


def package(lock, observed, writer, profile):
    source_tools = {}
    for name, pin in lock["tool_sha256"].items():
        path = SWROOT + name
        require(digest(git("show", f"{lock['source_revision']}:{path}")) == pin,
                "pre-writer native authoring script differs from the source lock")
        source_tools[path] = exact_object(writer, path)
    native_tools = source_tools | {THINROOT + name: exact_object(writer, THINROOT + name)
                                   for name in ("RunThinNative.py", "CompareThinNative.py")}
    require(all(digest(raw) == observed["files"]["Tools/" + Path(name).name] for name, raw in native_tools.items()),
            "comparison closure differs from the successful disclosed job")
    layout = BytesIO()
    with ZipFile(layout, "w", compression=ZIP_DEFLATED) as output:
        source = git("archive", "--format=tar", writer, "src")
        with open_tar(fileobj=BytesIO(source), mode="r:") as tracked:
            for member in tracked:
                if member.isdir():
                    continue
                require(member.isfile(), "writer source package must use ordinary tracked files")
                output.writestr(archive_path(member.name).as_posix(), tracked.extractfile(member).read())
        additional = () if profile == "front" else (THINROOT + "BuildThinPlanes.py", THINROOT + "ThinPlaneAudit.py")
        for pathname in RESEARCH + additional:
            output.writestr(pathname, exact_object(writer, pathname))
        for pathname, raw in source_tools.items():
            output.writestr(pathname, raw)
        names = output.namelist()
        require(len(names) == len({name.casefold() for name in names}), "writer package has colliding guest paths")
    return layout.getvalue()


def principal_inputs(directory, result, pin, baseline, lock):
    job_raw = checked(directory / "NativeJob.json", PRINCIPAL_JOB)
    build_raw = checked(directory / "BuildReceipt.json", PRINCIPAL_BUILD)
    native_raw = checked(result, pin)
    job = principal_disclosure(native_raw, pin, job_raw, build_raw, baseline)
    require(job["files"]["Control.SLDPRT"] == lock["control_sha256"], "principal job used a different bracket control")
    return job, {"PrincipalNative.json": native_raw, "PrincipalJob.json": job_raw, "PrincipalBuild.json": build_raw}


def freeze(output, disclosed_result, disclosed_job, control, guest, principal):
    output = output.resolve()
    require(not output.exists() and not output.is_relative_to(ROOT), "use a new packet outside the checkout")
    guest = guest_work(guest)
    profile = "front" if principal is None else "principal"
    writer, tree = WRITERS[profile]
    git("merge-base", "--is-ancestor", LOCK_REVISION, writer)
    require(git("rev-parse", f"{writer}:src").decode().strip() == tree,
            "writer tree differs from the disclosed successful revision")
    writer_at = int(git("show", "-s", "--format=%ct", writer))
    raw_lock = exact_object(writer, LOCK_RELATIVE)
    lock = source_lock(raw_lock)
    require(raw_lock == git("show", f"{LOCK_REVISION}:{LOCK_RELATIVE}")
            and lock["finished_at"] < writer_at, "source lock did not precede the writer")
    disclosed = checked(disclosed_result, DISCLOSURE_SHA)
    baseline = disclosure(disclosed)
    job_raw = checked(disclosed_job, DISCLOSURE_JOB_SHA)
    job = json.loads(job_raw)
    require((job["writer_revision"], job["writer_sdk_tree"]) == WRITERS["front"]
            and job["oracle_sha256"] == ORACLE and job["files"]["Control.SLDPRT"] == lock["control_sha256"],
            "successful disclosed job used a different writer or bracket control")
    control_bytes = checked(control, lock["control_sha256"])
    principal_evidence = {}
    if principal is not None:
        job, principal_evidence = principal_inputs(*principal, baseline, lock)
    packed = package(lock, job, writer, profile)
    tools = {name: (HERE / name).read_bytes() for name in STANDALONE}
    manifest = {"schema": SCHEMA, "profile": profile, "writer": writer, "writer_src_tree": tree,
                "source_lock_revision": LOCK_REVISION, "source_lock_sha256": LOCK_SHA,
                "disclosed_sha256": DISCLOSURE_SHA, "oracle_sha256": ORACLE, "code_sha256": digest(packed),
                "source_lock_finished_at": lock["finished_at"], "writer_commit_at": writer_at, "frozen_at": time(),
                "guest_work": str(guest), "private_inputs_read_during_freeze": 0,
                "supervisor": {name: digest(raw) for name, raw in tools.items()}}
    if principal_evidence:
        manifest["principal_native_sha256"] = digest(principal_evidence["PrincipalNative.json"])
    output.mkdir(parents=True)
    for name, raw in {"Code.zip": packed, "SourceLock.json": raw_lock, "DisclosedNative.json": disclosed, "DisclosedJob.json": job_raw,
                      "Control.SLDPRT": control_bytes, **principal_evidence, **tools}.items():
        publish(output / name, raw)
    return {"manifest_sha256": publish(output / "Manifest.json", encode(manifest)),
            "writer_revision": writer, "writer_src_tree": tree, "profile": profile,
            "expected_native_phases": 18, "private_inputs_read_during_freeze": 0}


if __name__ == "__main__":
    parser = ArgumentParser(description="Stage only the public controls and exact frozen thin writer")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--disclosed-result", type=Path, required=True)
    parser.add_argument("--disclosed-job", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--guest-work", required=True)
    parser.add_argument("--principal-packet", type=Path)
    parser.add_argument("--principal-result", type=Path)
    parser.add_argument("--principal-result-sha256")
    args = parser.parse_args()
    principal = (args.principal_packet, args.principal_result, args.principal_result_sha256)
    require(all(principal) or not any(principal), "principal evaluation requires a completed disclosed result and exact digests")
    print(encode(freeze(args.output, args.disclosed_result, args.disclosed_job, args.control, args.guest_work,
                        principal if all(principal) else None)).decode(), end="")
