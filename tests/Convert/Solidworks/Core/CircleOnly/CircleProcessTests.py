# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as LoadRecord
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe

from pytest import mark as TestMark

from tests.Convert.Solidworks.Core.CircleOnly.Samples import KCases, ReadCircleInput


# fresh isolated executions must preserve the same circle after its input file becomes unavailable
@TestMark.parametrize(
    ("CaseName", "PlaneId"), [(Entry[0], Entry[2]) for Entry in KCases]
)
def CheckSourceFree(TmpPath: FilePath, CaseName: str, PlaneId: int) -> None:
    SourcePath = TmpPath / "Source.SLDPRT"
    ModelPath = TmpPath / "Model.json"
    _ = SourcePath.write_bytes(ReadCircleInput(CaseName))
    ScriptPath = FilePath(__file__).with_name("CircleProcess.py")
    First = RunProcess(
        [PythonExe, str(ScriptPath), "read", str(SourcePath), str(ModelPath)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert First.returncode == 0, First.stderr
    SourcePath.unlink()
    Second = RunProcess(
        [PythonExe, str(ScriptPath), "replay", str(ModelPath)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Second.returncode == 0, Second.stderr
    assert (
        LoadRecord(First.stdout)
        == LoadRecord(Second.stdout)
        == {
            "bodies": 0,
            "entities": ["circle", "point"],
            "constraints": ["diameter", "coincident"],
            "support": f"sldprt:plane:{PlaneId}",
            "guarded": True,
        }
    )
