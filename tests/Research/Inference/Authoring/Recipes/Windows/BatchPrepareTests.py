# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from json import loads as DecodeJson
from pathlib import Path as FilePath

from pytest import mark as CaseMark

from tests.Research.Inference.Authoring.Recipes.Windows.PreparedPaths import (
    PreparedPaths,
)
from tests.Research.Inference.Authoring.Recipes.Windows.RunBatchProbe import (
    RunBatchProbe,
)


# deep session preparation must retain full source identities while keeping every future archive path within native limits
def CheckBatchPaths(TmpPath: FilePath) -> None:
    OutputPath = TmpPath / "Store/sessions" / ("a" * 16) / "work/Capture"
    Cases = [
        {"recipe": Recipe}
        for Recipe in (
            "extrude-two-direction",
            "extrude-midplane",
            "extrude-offset-start",
        )
    ]
    Process = RunBatchProbe(TmpPath, OutputPath, Cases)
    assert Process.returncode == 0, Process.stderr
    Prepared = DecodeJson(Process.stdout)
    ManifestPath = FilePath(Prepared["manifest"])
    assert (
        Prepared["manifest_sha256"] == HashBytes(ManifestPath.read_bytes()).hexdigest()
    )
    Manifest = DecodeJson(ManifestPath.read_bytes())
    assert Manifest["schema"] == 1 and len(Manifest["cases"]) == 3
    for Index, Entry in enumerate(Manifest["cases"]):
        Configuration = FilePath(Entry["configuration"])
        Content = Configuration.read_bytes()
        Digest = HashBytes(Content).hexdigest()
        assert len(Digest) == 64 and Prepared["configuration_sha256"][Index] == Digest
        assert Configuration.parent.name == "Case" + Digest[:16]
        assert (
            Prepared["outputs"][Index] == Entry["output"] == str(Configuration.parent)
        )
        assert DecodeJson(Content) == Prepared["cases"][Index]
        Archives = PreparedPaths(Prepared["cases"][Index], Configuration.parent)
        assert all(
            len(str(Archive).encode("utf-16-le")) // 2 < 260 for Archive in Archives
        )
        assert all(not Archive.exists() for Archive in Archives)


# repeated canonical cases must fail before creating an output directory or starting any native application
def CheckBatchDup(TmpPath: FilePath) -> None:
    OutputPath = TmpPath / "Capture"
    Process = RunBatchProbe(
        TmpPath,
        OutputPath,
        [
            {"recipe": "extrude-midplane"},
            {"recipe": "extrude-midplane", "parameters": {"depth_mm": 10.0}},
        ],
    )
    assert Process.returncode != 0
    assert "cannot repeat a configured case" in Process.stderr
    assert not OutputPath.exists()


# excessive native path length must be rejected without creating even the output directory
@CaseMark.parametrize("Folder", ("x" * 180, "\U0001f4c1" * 90))
def CheckBatchLong(TmpPath: FilePath, Folder: str) -> None:
    OutputPath = TmpPath / Folder / "Capture"
    Process = RunBatchProbe(TmpPath, OutputPath, [{"recipe": "extrude-midplane"}])
    assert Process.returncode != 0
    assert "native archive path exceeds the application limit" in Process.stderr
    assert not OutputPath.exists()
