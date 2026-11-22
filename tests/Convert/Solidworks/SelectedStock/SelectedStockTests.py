from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue


# the measured part must survive the normal registry and native owner reader in an isolated process
def TestStockRoute() -> None:
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
    Report = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert Report["runtime_input_file_reads"] == 0
    assert Report["staged_output_opens"] == 0
    assert Report["publications"] in (0, 3)
    Measured, Unmeasured = CastValue(list[dict[str, object]], Report["cases"])
    assert len(CastValue(dict[str, object], Measured["streams"])) == 10
    assert len(CastValue(dict[str, object], Unmeasured["streams"])) == 10
    assert Measured["sha256"] != Unmeasured["sha256"]
    assert "crossed_typed_selector" in CastValue(dict[str, str], Report["refusals"])
    RoundTrip = CastValue(dict[str, object], Report["readback_roundtrip"])
    assert RoundTrip["exact_regenerations"] == 5
    assert RoundTrip["publications"] == (10 if Report["publications"] else 0)
    assert RoundTrip["geometry_free_body_counts"] == {"design_only": 2, "raw_only": 2}
    assert (
        RoundTrip["runtime_input_file_reads"] == RoundTrip["staged_output_opens"] == 0
    )
    assert len(CastValue(dict[str, str], RoundTrip["refusals"])) == 6
