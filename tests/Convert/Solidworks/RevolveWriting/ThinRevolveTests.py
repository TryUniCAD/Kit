from json import loads as LoadJson
from os import name as OsName
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe
from typing import cast as CastValue

from pytest import mark as MarkTests


# disclosed front and right sweeps reach both public routes under the same complete suite
def TestThinRevolve() -> None:
    RootValue = FilePath(__file__).resolve().parents[4]
    Worker = RootValue / "re/tooling/sw2026/revolve/CheckThinSuiteCase.py"
    for RoleValue, NameValue in (
        ("front", "ThinUnequal"),
        ("principal", "ThinRightCenterControl"),
    ):
        Result = RunProcess(
            (PythonExe, "-I", "-B", str(Worker), "--case", RoleValue),
            cwd=RootValue,
            capture_output=True,
            text=True,
            check=False,
        )
        assert Result.returncode == 0, Result.stderr
        Report = CastValue(dict[str, object], LoadJson(Result.stdout))
        assert Report["case"] == NameValue
        IsExact = Report["exact_native_hash"]
        assert isinstance(IsExact, bool)
        if not IsExact:
            assert "zlib-ng" in str(Report["runtime_encoder"])
        assert Report["matching_streams"] == 10
        assert Report["strict_read_modes"] == 2
        assert Report["stream_routes"] == (6 if IsExact else 0)
        assert Report["stream_measurement_refusals"] == (0 if IsExact else 12)
        assert Report["file_routes"] == (2 if OsName == "nt" and IsExact else 0)
        assert Report["file_refusals"] == (4 if OsName == "nt" and not IsExact else 0)
        assert Report["name_contrasts"] == 4
        assert Report["unmeasured_refusals"] == 2
        assert Report["native_launches"] == 0
        assert Report["runtime"] == {
            "external_launches": 0,
            "input_file_reads": 0,
            "output_opens": 0,
        }


# genuine vendor saves exercise the strict guard and explicit partial routes in the shared process suite
@MarkTests.parametrize(
    "CaseName",
    (
        "ThinQueueFrontOriginal",
        "ThinQueueFrontEdited",
        "ThinQueueRightOriginal",
        "ThinQueueRightEdited",
    ),
)
def TestSavedThin(CaseName: str) -> None:
    RootValue = FilePath(__file__).resolve().parents[4]
    Worker = RootValue / "re/tooling/sw2026/revolve/CheckSavedThinSuite.py"
    Result = RunProcess(
        (PythonExe, "-I", "-B", str(Worker), "--case", CaseName),
        cwd=RootValue,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
    assert Result.returncode == 0, Result.stderr
    Report = CastValue(dict[str, object], LoadJson(Result.stdout))
    assert Report["case"] == CaseName
    assert Report["strict_refusals"] == 2
    assert Report["partial_permissive_reads"] == 2
    assert Report["raw_payloads"] == 2
    assert Report["native_launches"] == 0
    assert Report["runtime"] == {
        "external_launches": 0,
        "input_file_reads": 0,
        "output_opens": 0,
    }
