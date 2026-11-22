from __future__ import annotations

from hashlib import sha256 as HashBytes
from io import BytesIO as ByteStream
from os import environ as EnvValues
from re import fullmatch as FullMatch
from subprocess import run as RunProcess
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# historical object reads need one fetch for all missing pinned blobs in partial checkouts
def HydrateFrozen(Objects: list[str], InputData: bytes) -> None:
    Outcome = RunProcess(
        ["git", "cat-file", "--batch-check=%(objectname) %(objecttype)"],
        cwd=KRepoRoot,
        env=EnvValues.copy() | {"GIT_NO_LAZY_FETCH": "1"},
        input=InputData,
        capture_output=True,
        check=True,
        timeout=30,
    )
    MissingIds = set[str]()
    LinesValue = Outcome.stdout.decode("ascii").splitlines()
    for ObjectId, LineValue in zip(Objects, LinesValue, strict=True):
        assert LineValue in (ObjectId + " blob", ObjectId + " missing")
        if LineValue.endswith(" missing"):
            MissingIds.add(ObjectId)
    if MissingIds:
        _ = RunProcess(
            [
                "git",
                "-c",
                "protocol.version=2",
                "fetch",
                "--filter=blob:none",
                "--no-tags",
                "--no-write-fetch-head",
                "--no-recurse-submodules",
                "--stdin",
                "origin",
            ],
            cwd=KRepoRoot,
            input=("\n".join(sorted(MissingIds)) + "\n").encode("ascii"),
            capture_output=True,
            check=True,
            timeout=60,
        )


# source restoration must reject missing objects or changed bytes before executing historical code
def ReadGitSource(Entries: list[dict[str, object]]) -> dict[str, bytes]:
    Objects = [CastValue(str, Entry["git_blob"]) for Entry in Entries]
    assert all(FullMatch(r"[0-9a-f]{40}", Value) for Value in Objects)
    InputData = ("\n".join(Objects) + "\n").encode("ascii")
    HydrateFrozen(Objects, InputData)
    Outcome = RunProcess(
        ["git", "cat-file", "--batch"],
        cwd=KRepoRoot,
        env=EnvValues.copy() | {"GIT_NO_LAZY_FETCH": "1"},
        input=InputData,
        capture_output=True,
        check=True,
        timeout=60,
    )
    StreamValue = ByteStream(Outcome.stdout)
    Results: dict[str, bytes] = {}
    for Entry in Entries:
        ObjectName, ObjectKind, ObjectBytes = StreamValue.readline().decode().split()
        assert ObjectName == Entry["git_blob"] and ObjectKind == "blob"
        assert int(ObjectBytes) == Entry["bytes"]
        RawValue = StreamValue.read(int(ObjectBytes))
        assert len(RawValue) == Entry["bytes"]
        assert HashBytes(RawValue).hexdigest() == Entry["sha256"]
        assert StreamValue.read(1) == b"\n"
        PathName = CastValue(str, Entry["path"])
        assert PathName not in Results
        Results[PathName] = RawValue
    assert StreamValue.read() == b""
    return Results
