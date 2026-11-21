from argparse import ArgumentParser
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import subprocess

from SealedCylinderPacket import (
    AUTHOR_TOOLS,
    COMPARATOR_REVISION,
    CONSTRUCTION_PATH,
    CONSTRUCTION_SHA256,
    CONTROL,
    GUARD_FILES,
    IMPORT_TOOLS,
    LOCK_PATH,
    LOCK_REVISION,
    LOCK_SHA256,
    LOCK_TRANSPORT_SHA256,
    ORACLE,
    PROTOCOL_TOOLS,
    SCHEMA,
    SOURCE_ROOT,
    VERSION,
    WRITER_REVISION,
    checked,
    digest,
    encode,
    guest_directory,
    is_revision,
    require,
    source_lock,
)

ROOT = Path(__file__).resolve().parents[4]
RESEARCH = PurePosixPath("re/tooling/sw2026")
IMPORTS = RESEARCH / "imported_body_source"


def git(*args, input_data=None):
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        input=input_data,
        check=True,
        capture_output=True,
    ).stdout


def tracked_file(revision, name):
    require(is_revision(revision), "supply a full committed tool revision")
    selection = git("ls-tree", revision, "--", str(name)).split()
    require(
        selection[:2] in ([b"100644", b"blob"], [b"100755", b"blob"]),
        "frozen tool must be a tracked regular file",
    )
    return git("cat-file", "blob", selection[2].decode("ascii"))


def code_entries(revision):
    tree = git("ls-tree", "-rz", revision, "--", "src", *GUARD_FILES)
    records = []
    for entry in tree.rstrip(b"\0").split(b"\0"):
        info, raw = entry.split(b"\t", 1)
        mode, kind, oid = info.split()
        name = raw.decode("utf-8")
        path = PurePosixPath(name)
        require(
            mode in (b"100644", b"100755")
            and kind == b"blob"
            and not path.is_absolute()
            and ".." not in path.parts
            and (name.startswith("src/") or name in GUARD_FILES),
            "frozen SDK closure requires ordinary tracked files",
        )
        records.append((oid, name))
    names = [name for _, name in records]
    require(
        set(GUARD_FILES) <= set(names)
        and len({name.casefold() for name in names}) == len(names),
        "frozen SDK closure has a missing guard or ambiguous Windows member",
    )
    with BytesIO(
        git(
            "cat-file",
            "--batch",
            input_data=b"".join(oid + b"\n" for oid, _ in records),
        )
    ) as stream:
        for oid, name in records:
            actual, kind, length = stream.readline().split()
            require(
                oid == actual and kind == b"blob", "frozen SDK object identity differs"
            )
            content = stream.read(int(length))
            require(
                len(content) == int(length) and stream.read(1) == b"\n",
                "frozen SDK object framing differs",
            )
            yield "Code/" + name, content
        require(not stream.read(), "unexpected object after the frozen SDK closure")


def tool_entries(revision, lock):
    for name in (*AUTHOR_TOOLS, *IMPORT_TOOLS):
        if name in lock["tools_sha256"]:
            origin = lock["source_revision"]
            source = RESEARCH if name in AUTHOR_TOOLS else IMPORTS
            content = tracked_file(origin, source / name)
            require(
                digest(content) == lock["tools_sha256"][name],
                "frozen source author tool differs",
            )
        else:
            content = tracked_file(COMPARATOR_REVISION, IMPORTS / name)
        yield "Tools/" + name, content
    for name in PROTOCOL_TOOLS:
        yield "Tools/" + name, tracked_file(revision, IMPORTS / name)


def stage(args):
    require(
        args.writer_revision == WRITER_REVISION,
        "use the exact committed cylinder constructor",
    )
    require(
        is_revision(args.protocol_revision), "supply the committed evaluator revision"
    )
    for revision in (args.writer_revision, args.protocol_revision):
        git("merge-base", "--is-ancestor", LOCK_REVISION, revision)
    git("merge-base", "--is-ancestor", WRITER_REVISION, args.protocol_revision)
    writer_time = int(git("show", "-s", "--format=%ct", WRITER_REVISION))
    receipt = tracked_file(LOCK_REVISION, LOCK_PATH)
    lock = source_lock(receipt)
    require(
        0 < lock["source_batch_locked_at_unix_s"] < writer_time < 2**31,
        "writer must postdate both private source locks",
    )
    construction = tracked_file(WRITER_REVISION, CONSTRUCTION_PATH)
    require(
        digest(construction) == CONSTRUCTION_SHA256,
        "constructor revision does not bind the disclosed host proof",
    )
    guest = guest_directory(args.guest_root)
    require(
        not args.destination.is_symlink(),
        "choose an unused ordinary external packet",
    )
    target = args.destination.resolve()
    require(
        not target.exists() and not target.is_relative_to(ROOT),
        "choose an unused external packet",
    )
    control = checked(args.control, CONTROL)
    target.mkdir()
    for name, content in (
        ("SourceLock.json", receipt),
        ("Construction.json", construction),
        ("Control.SLDPRT", control),
    ):
        with (target / name).open("xb") as output:
            output.write(content)
    digests = {}
    for name, content in (
        *code_entries(WRITER_REVISION),
        *tool_entries(args.protocol_revision, lock),
    ):
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as output:
            output.write(content)
        digests[name] = digest(content)
    job = encode(
        {
            "schema": SCHEMA,
            "writer_revision": WRITER_REVISION,
            "writer_committed_at": writer_time,
            "protocol_revision": args.protocol_revision,
            "source_lock_revision": LOCK_REVISION,
            "source_lock_sha256": LOCK_SHA256,
            "source_transport_sha256": LOCK_TRANSPORT_SHA256,
            "construction_sha256": CONSTRUCTION_SHA256,
            "oracle_version": VERSION,
            "oracle_sha256": ORACLE,
            "control_sha256": CONTROL,
            "guest_root": str(guest),
            "source_root": str(SOURCE_ROOT),
            "files_sha256": digests,
        }
    )
    with (target / "Job.json").open("xb") as output:
        output.write(job)
    print(json.dumps({"job_sha256": digest(job), "frozen_files": len(digests)}))


def main():
    parser = ArgumentParser(
        description="Freeze the private periodic import evaluation without the original inputs"
    )
    parser.add_argument("destination", type=Path)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--writer-revision", default=WRITER_REVISION)
    parser.add_argument("--protocol-revision", required=True)
    parser.add_argument("--guest-root", required=True)
    stage(parser.parse_args())


if __name__ == "__main__":
    main()
