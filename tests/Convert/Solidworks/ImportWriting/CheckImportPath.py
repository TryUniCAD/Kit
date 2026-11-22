from json import loads as LoadJson
from os import environ as Environment
from subprocess import run as RunProcess
from sys import executable as PythonExec
from zlib import ZLIB_RUNTIME_VERSION as DeflateRuntime

from pytest import skip as SkipCase

from tests.Convert.Api.ApiTestPaths import KRootPath


# exercise the measured physical path through both public write routes
def CheckImportPath(ProfileName: str, ExpectedSize: int) -> None:
    ScriptPath = (
        KRootPath / "re/tooling/sw2026/imported_body_source/VerifyMeasuredBoxPaths.py"
    )
    RuntimePath = Environment.get("KIT_MEASURED_PART_PYTHON")
    if (
        not RuntimePath
        and "zlib-ng" in DeflateRuntime
        and Environment.get("GITHUB_ACTIONS") != "true"
    ):
        SkipCase("measured Windows publication requires the matching runtime")
    Outcome = RunProcess(
        (
            RuntimePath or PythonExec,
            "-I",
            "-B",
            str(ScriptPath),
            "--profile",
            ProfileName,
        ),
        capture_output=True,
        encoding="utf-8",
        timeout=90,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = LoadJson(Outcome.stdout)
    assert ReportValue["exact_publications"] == 2
    assert ReportValue["runtime_input_file_reads"] == 0
    assert not ReportValue["declared_locator_option_used"]
    assert ReportValue["routes"]["direct"] == ReportValue["routes"]["registry"]
    assert ReportValue["routes"]["direct"]["bytes"] == ExpectedSize
