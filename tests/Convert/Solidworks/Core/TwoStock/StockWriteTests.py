from json import loads as LoadRecord
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe
from typing import cast as CastValue

from pytest import mark as TestMark


# ordinary preparation must preserve selected stock ownership while public refusals leave destinations intact
@TestMark.parametrize("RequestRole", ("disclosed", "independent", "refusals"))
def TestStockWrite(RequestRole: str) -> None:
    RootValue = FilePath(__file__).resolve().parents[5]
    ScriptPath = (
        RootValue
        / "re/tooling/sw2026/throughsource/twostockgraph/ProveQualifiedStocks.py"
    )
    ChildValue = RunProcess(
        (PythonExe, "-I", "-B", str(ScriptPath), "--worker", RequestRole),
        cwd=RootValue,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert ChildValue.returncode == 0, ChildValue.stderr
    ReportValue = CastValue(dict[str, object], LoadRecord(ChildValue.stdout))
    assert ReportValue["runtime_input_file_reads"] == 0
    if RequestRole == "refusals":
        assert ReportValue["staged_refusals"] == 2
        assert ReportValue["prior_destinations_preserved"] is True
        assert ReportValue["no_staging_remains"] is True
    else:
        assert ReportValue["qualified_routes"] == 0
        assert ReportValue["prepared_routes"] == ReportValue["missing_receipt_refusals"] == 4
        RequiredCaps = CastValue(list[str], ReportValue["intended_capabilities"])
        assert len(RequiredCaps) == 7 and "selections" in RequiredCaps
