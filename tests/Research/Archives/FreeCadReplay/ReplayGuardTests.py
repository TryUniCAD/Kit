# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as ParseJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe

from pytest import mark as MarkValue

from tests.Research.Archives.FreeCadReplay.MakeReplay import MakeReplay

# each child resolves the checkout owning the actual source binding and write policy
KRepoRoot = FilePath(__file__).resolve().parents[4]


# source bound replay must remain distinct from reconstruction and native qualification
@MarkValue.parametrize(
    "CaseName",
    (
        "unchanged",
        "supported",
        "strict",
        "strict-path",
        "source-bytes",
        "rebuild",
        "semantic",
        "source-hash",
        "binding",
        "snapshot",
        "fresh",
        "overwrite",
        "overwrite-allowed",
    ),
)
def CheckReplay(TmpPath: FilePath, CaseName: str) -> None:
    SourcePath = TmpPath / "Source.FCStd"
    Original = MakeReplay(CaseName)
    assert SourcePath.write_bytes(Original) == len(Original)
    Process = RunProcess(
        [
            PythonExe,
            "-B",
            "-m",
            "tests.Research.Archives.FreeCadReplay.ObserveReplay",
            str(SourcePath),
            CaseName,
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Process.returncode == 0, Process.stderr + Process.stdout
    Report = ParseJson(Process.stdout)
    assert Report["refused"] is (
        CaseName not in {"unchanged", "supported", "overwrite-allowed"}
    )
    assert Report["source_unchanged"] is True and SourcePath.read_bytes() == Original
