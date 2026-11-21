from argparse import ArgumentParser
from io import BytesIO
import json
from pathlib import Path
from subprocess import check_output
from tarfile import open as open_tar
from time import time
from zipfile import ZIP_DEFLATED, ZipFile

from ThinHeldoutPacket import (
    DISCLOSURE_JOB_SHA, DISCLOSURE_SHA, LOCK_RELATIVE, LOCK_REVISION, LOCK_SHA, ORACLE, SCHEMA, STANDALONE,
    SWROOT, THINROOT, WRITER, WRITER_TREE, archive_path, checked, digest, disclosure,
    encode, guest_work, publish, require, source_lock,
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


def exact_object(path):
    return git("show", f"{WRITER}:{path}")


def package(lock, observed):
    source_tools = {}
    for name, pin in lock["tool_sha256"].items():
        path = SWROOT + name
        require(digest(git("show", f"{lock['source_revision']}:{path}")) == pin,
                "pre-writer native authoring script differs from the source lock")
        source_tools[path] = exact_object(path)
    native_tools = source_tools | {THINROOT + name: exact_object(THINROOT + name)
                                   for name in ("RunThinNative.py", "CompareThinNative.py")}
    require(all(digest(raw) == observed["files"]["Tools/" + Path(name).name] for name, raw in native_tools.items()),
            "comparison closure differs from the successful disclosed job")
    layout = BytesIO()
    with ZipFile(layout, "w", compression=ZIP_DEFLATED) as output:
        source = git("archive", "--format=tar", WRITER, "src")
        with open_tar(fileobj=BytesIO(source), mode="r:") as tracked:
            for member in tracked:
                if member.isdir():
                    continue
                require(member.isfile(), "writer source package must use ordinary tracked files")
                output.writestr(archive_path(member.name).as_posix(), tracked.extractfile(member).read())
        for pathname in RESEARCH:
            output.writestr(pathname, exact_object(pathname))
        for pathname, raw in source_tools.items():
            output.writestr(pathname, raw)
        names = output.namelist()
        require(len(names) == len({name.casefold() for name in names}), "writer package has colliding guest paths")
    return layout.getvalue()


def freeze(output, disclosed_result, disclosed_job, control, guest):
    output = output.resolve()
    require(not output.exists() and not output.is_relative_to(ROOT), "use a new packet outside the checkout")
    guest = guest_work(guest)
    git("merge-base", "--is-ancestor", LOCK_REVISION, WRITER)
    require(git("rev-parse", f"{WRITER}:src").decode().strip() == WRITER_TREE,
            "writer tree differs from the disclosed successful revision")
    writer_at = int(git("show", "-s", "--format=%ct", WRITER))
    raw_lock = exact_object(LOCK_RELATIVE)
    lock = source_lock(raw_lock)
    require(raw_lock == git("show", f"{LOCK_REVISION}:{LOCK_RELATIVE}")
            and lock["finished_at"] < writer_at, "source lock did not precede the writer")
    disclosed = checked(disclosed_result, DISCLOSURE_SHA)
    disclosure(disclosed)
    job_raw = checked(disclosed_job, DISCLOSURE_JOB_SHA)
    job = json.loads(job_raw)
    require(job["writer_revision"] == WRITER and job["writer_sdk_tree"] == WRITER_TREE
            and job["oracle_sha256"] == ORACLE and job["files"]["Control.SLDPRT"] == lock["control_sha256"],
            "successful disclosed job used a different writer or bracket control")
    control_bytes = checked(control, lock["control_sha256"])
    packed = package(lock, job)
    tools = {name: (HERE / name).read_bytes() for name in STANDALONE}
    manifest = {"schema": SCHEMA, "writer": WRITER, "writer_src_tree": WRITER_TREE,
                "source_lock_revision": LOCK_REVISION, "source_lock_sha256": LOCK_SHA,
                "disclosed_sha256": DISCLOSURE_SHA, "oracle_sha256": ORACLE, "code_sha256": digest(packed),
                "source_lock_finished_at": lock["finished_at"], "writer_commit_at": writer_at, "frozen_at": time(),
                "guest_work": str(guest), "private_inputs_read_during_freeze": 0,
                "supervisor": {name: digest(raw) for name, raw in tools.items()}}
    output.mkdir(parents=True)
    for name, raw in {"Code.zip": packed, "SourceLock.json": raw_lock, "DisclosedNative.json": disclosed, "DisclosedJob.json": job_raw,
                      "Control.SLDPRT": control_bytes, **tools}.items():
        publish(output / name, raw)
    return {"manifest_sha256": publish(output / "Manifest.json", encode(manifest)),
            "writer_revision": WRITER, "writer_src_tree": WRITER_TREE,
            "expected_native_phases": 18, "private_inputs_read_during_freeze": 0}


if __name__ == "__main__":
    parser = ArgumentParser(description="Stage only the public controls and exact frozen thin writer")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--disclosed-result", type=Path, required=True)
    parser.add_argument("--disclosed-job", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--guest-work", required=True)
    args = parser.parse_args()
    print(encode(freeze(args.output, args.disclosed_result, args.disclosed_job, args.control, args.guest_work)).decode(), end="")
