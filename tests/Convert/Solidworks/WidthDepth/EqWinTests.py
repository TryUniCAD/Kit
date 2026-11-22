from os import environ as Environment
from sys import platform as PlatformValue

from pytest import mark as MarkCase

from tests.Convert.Solidworks.WidthDepth.MeasuredEqTests import AssertEqRead, RunEqCase


# the selected windows shard must reproduce the measured archive through all four public stream routes
@MarkCase.skipif(
    PlatformValue != "win32", reason="the positive fixture is scheduled on Windows"
)
def TestEqWin() -> None:
    RuntimePath = Environment.get("KIT_MEASURED_PART_PYTHON")
    assert RuntimePath, "the Windows shard must provide the measured part runtime"
    Report, Digest = RunEqCase(RuntimePath)
    assert Report["sha256"] == Digest
    assert Report["published_routes"] == 4
    AssertEqRead(Report, Digest)
