from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

import pytest as Pytest


# share the isolated process report between refusal and exact publication coverage
@Pytest.fixture(scope="module")
def StockReport() -> dict[str, object]:
    RepoRoot = FilePath(__file__).resolve().parents[4]
    Script = RepoRoot / "re/tooling/sw2026/throughsource/CheckMeasuredSelectedStocks.py"
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(Script)),
        capture_output=True,
        encoding="utf-8",
        timeout=90,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    return CastValue(dict[str, object], LoadJson(Outcome.stdout))


# both compressors must check semantic readback and guard unmeasured publication
def TestStockRoute(StockReport: dict[str, object]) -> None:
    Report = StockReport
    assert Report["runtime_input_file_reads"] == 0
    assert Report["staged_output_opens"] == 0
    assert Report["publications"] in (0, 3)
    Measured, Unmeasured = CastValue(list[dict[str, object]], Report["cases"])
    assert len(CastValue(dict[str, object], Measured["streams"])) == 10
    assert len(CastValue(dict[str, object], Unmeasured["streams"])) == 10
    assert Measured["sha256"] != Unmeasured["sha256"]
    assert "crossed_typed_selector" in CastValue(dict[str, str], Report["refusals"])
    Portable = CastValue(dict[str, object], Report["portable_json"])
    assert set(Portable) == {"direct", "registry"}
    assert Portable["direct"] == Portable["registry"]
    RoundTrip = CastValue(dict[str, object], Report["readback_roundtrip"])
    assert RoundTrip["exact_regenerations"] == 5
    assert RoundTrip["publications"] == (10 if Report["publications"] else 0)
    assert RoundTrip["geometry_free_body_counts"] == {"design_only": 2, "raw_only": 2}
    assert (
        RoundTrip["runtime_input_file_reads"] == RoundTrip["staged_output_opens"] == 0
    )
    assert len(CastValue(dict[str, str], RoundTrip["refusals"])) == 6


# exact publication needs separate evidence from alternate compressor refusal
def TestExactStock(StockReport: dict[str, object]) -> None:
    if StockReport["publications"] == 0 and "zlib-ng" in str(StockReport["compressor"]):
        Pytest.skip("alternate compressor exercised refusal, not measured publication")
    assert StockReport["publications"] == 3
    RoundTrip = CastValue(dict[str, object], StockReport["readback_roundtrip"])
    assert RoundTrip["publications"] == 10
