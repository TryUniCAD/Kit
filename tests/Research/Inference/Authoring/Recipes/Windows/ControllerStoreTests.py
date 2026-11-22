# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from json import loads as DecodeJson
from pathlib import Path as FilePath
from sys import platform as Platform

from pytest import mark as CaseMark

from tests.Research.Inference.Authoring.Recipes.Windows.RunController import (
    RunController,
)


# real windows publication must deduplicate files and preserve an already published immutable object
@CaseMark.skipif(
    Platform != "win32",
    reason="requires the actual Windows filesystem publication path",
)
def CheckStoreFiles(TmpPath: FilePath) -> None:
    StorePath = TmpPath / "Store"
    Created = RunController(StorePath, "init")
    assert Created.returncode == 0, Created.stderr
    Content = b"actual controller immutable artifact publication\n" * 2048
    SourcePath = TmpPath / "Input.bin"
    _ = SourcePath.write_bytes(Content)
    Expected = HashBytes(Content).hexdigest()
    First = RunController(StorePath, "bind", "first-input", SourcePath)
    assert First.returncode == 0, First.stderr
    assert DecodeJson(First.stdout)["sha256"] == Expected
    Verified = RunController(StorePath, "artifact", Expected)
    assert Verified.returncode == 0, Verified.stderr
    NativePath = FilePath(DecodeJson(Verified.stdout)["path"])
    Before = NativePath.stat()
    RepeatedPath = TmpPath / "Repeated.bin"
    _ = RepeatedPath.write_bytes(Content)
    Second = RunController(StorePath, "bind", "second-input", RepeatedPath)
    assert Second.returncode == 0, Second.stderr
    assert DecodeJson(Second.stdout)["sha256"] == Expected
    Repeated = RunController(StorePath, "artifact", Expected)
    assert Repeated.returncode == 0, Repeated.stderr
    assert DecodeJson(Repeated.stdout)["size_bytes"] == len(Content)
    assert NativePath.read_bytes() == Content
    After = NativePath.stat()
    assert (Before.st_ino, Before.st_mtime_ns) == (After.st_ino, After.st_mtime_ns)


# a conflicting existing object must stay rejected rather than being silently replaced by valid incoming bytes
@CaseMark.skipif(
    Platform != "win32",
    reason="requires the actual Windows filesystem publication path",
)
def CheckStoreClash(TmpPath: FilePath) -> None:
    StorePath = TmpPath / "Store"
    Created = RunController(StorePath, "init")
    assert Created.returncode == 0, Created.stderr
    SourcePath = TmpPath / "Input.bin"
    Content = b"immutable artifact whose existing object must be verified"
    _ = SourcePath.write_bytes(Content)
    Bound = RunController(StorePath, "bind", "first-input", SourcePath)
    assert Bound.returncode == 0, Bound.stderr
    Digest = DecodeJson(Bound.stdout)["sha256"]
    ObjectPath = StorePath / "objects" / Digest[:2] / Digest
    Corrupt = b"conflicting existing immutable object"
    _ = ObjectPath.write_bytes(Corrupt)
    Before = ObjectPath.stat()
    Rejected = RunController(StorePath, "bind", "second-input", SourcePath)
    assert Rejected.returncode == 1
    assert "artifact integrity mismatch" in Rejected.stderr
    Verified = RunController(StorePath, "artifact", Digest)
    assert Verified.returncode == 1 and "artifact integrity mismatch" in Verified.stderr
    assert ObjectPath.read_bytes() == Corrupt
    After = ObjectPath.stat()
    assert (Before.st_ino, Before.st_mtime_ns) == (After.st_ino, After.st_mtime_ns)
