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
from tests.Research.Inference.Authoring.Recipes.Windows.RunProducers import RunProducers


# simultaneous actual producers must converge on one verified object while preserving any earlier publication
@CaseMark.skipif(
    Platform != "win32",
    reason="requires the actual Windows filesystem publication path",
)
@CaseMark.parametrize("Preexisting", (False, True))
def CheckConcurrent(TmpPath: FilePath, Preexisting: bool) -> None:
    StorePath = TmpPath / "Store"
    Created = RunController(StorePath, "init")
    assert Created.returncode == 0, Created.stderr
    InputPath = TmpPath / "Input.bin"
    Content = b"concurrent immutable object publication\n" * 4096
    _ = InputPath.write_bytes(Content)
    Digest = HashBytes(Content).hexdigest()
    ObjectPath = StorePath / "objects" / Digest[:2] / Digest
    Before = None
    if Preexisting:
        Bound = RunController(StorePath, "bind", "initial-input", InputPath)
        assert Bound.returncode == 0, Bound.stderr
        Before = ObjectPath.stat()
    Reports = RunProducers(TmpPath, StorePath, InputPath)
    assert Reports == [{"sha256": Digest, "size_bytes": len(Content)}] * 4
    Verified = RunController(StorePath, "artifact", Digest)
    assert Verified.returncode == 0, Verified.stderr
    assert DecodeJson(Verified.stdout)["sha256"] == Digest
    assert ObjectPath.read_bytes() == Content
    assert not list((StorePath / "objects").glob("tmp*"))
    if Before is not None:
        After = ObjectPath.stat()
        assert (Before.st_ino, Before.st_mtime_ns) == (After.st_ino, After.st_mtime_ns)
