from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue


# the real research preparation and strict sdk readback must agree on absolute millimetres for each supported input unit
def TestDepthUnits() -> None:
    RootPath = FilePath(__file__).resolve().parents[3]
    Outcome = RunProcess(
        (
            PythonExec,
            "-I",
            "-B",
            str(RootPath / "re/solidworks/EncoderBoundary/CheckDepthUnits.py"),
            "--root",
            str(RootPath),
        ),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert ReportValue["fresh_processes"] == 2
    assert ReportValue["native_launches"] == 0
    RowsValue = CastValue(list[dict[str, object]], ReportValue["results"])
    assert {RowValue["source_unit"] for RowValue in RowsValue} == {"m", "in"}
    for RowValue in RowsValue:
        assert RowValue["source_unchanged"] is True
        assert RowValue["external_access_attempts"] == 0
        assert RowValue["prepared_depth_unit"] == "mm"
        assert RowValue["edited_depth_m_binary64"] == (19.87 * 0.001).hex()
        assert RowValue["strict_volume_mm3"] == 10531.1
        assert RowValue["exact_no_op_refused"] is (RowValue["source_unit"] == "m")
    assert len({RowValue["candidate_sha256"] for RowValue in RowsValue}) == 1
