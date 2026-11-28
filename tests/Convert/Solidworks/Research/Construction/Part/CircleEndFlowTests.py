from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Construction.Part.RunCirclePhase import (
    RunCirclePhase,
)


# native circular boss integration covers independent end drivers principal support frames and complete archive round trips
def TestCircleEnds(TmpPath: FilePath) -> None:
    InputsValue = TmpPath / "CircleEndInputs"
    Process = RunProcess(
        [
            PythonExec,
            "-I",
            "-B",
            str(KRepoRoot / "re/tooling/sw2026/AuthorSdkCircleRequests.py"),
            str(InputsValue),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Process.returncode == 0, Process.stderr
    for NameValue, ModeValue, IsReversed in (
        ("reverse-right", "blind", True),
        ("mid-top", "mid_plane", False),
        ("two-front", "two_directions", False),
        ("two-rev-top", "two_directions", True),
    ):
        Request = CastValue(
            dict[str, object],
            LoadJson((InputsValue / f"{NameValue}.json").read_bytes()),
        )
        BuildValue = RunCirclePhase(Request, "build")
        Prepared = RunCirclePhase({**Request, "build": BuildValue}, "prepare")
        AssertCircFlow(BuildValue, Prepared, ModeValue, IsReversed)


# the tested stream set and actual parameter ownership must agree with each authored termination
def AssertCircFlow(
    BuildValue: dict[str, object],
    Prepared: dict[str, object],
    ModeValue: str,
    IsReversed: bool,
) -> None:
    for Report in (BuildValue, Prepared):
        assert Report["passed"] is True and Report["runtime_input_file_reads"] == 0
        assert Report["sdk_runtime_research_imports"] == 0
    assert Prepared["exact_repacked_archive"] is True
    Streams = CastValue(dict[str, dict[str, object]], Prepared["streams"])
    assert len(Streams) == 10 and all(
        RowValue["byte_identity"] for RowValue in Streams.values()
    )
    Dimensions = CastValue(dict[str, object], Prepared["dimensions"])
    assert Dimensions["end_condition"] == ModeValue
    assert Dimensions["reverse_direction"] is IsReversed
    DepthValues = CastValue(list[dict[str, object]], Prepared["native_depths"])
    assert [RowValue["name"] for RowValue in DepthValues] == ["D1", "D2"]
    assert [RowValue["active"] for RowValue in DepthValues] == [
        True,
        ModeValue == "two_directions",
    ]
