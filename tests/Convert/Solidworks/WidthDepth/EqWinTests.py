from os import environ as Environment
from sys import platform as PlatformValue

from pytest import mark as MarkCase, skip as SkipCase

from tests.Convert.Solidworks.WidthDepth.AssertEqRead import AssertEqRead
from tests.Convert.Solidworks.WidthDepth.RunEqCase import RunEqCase


# the selected windows shard must reproduce the measured archive through all four public stream routes
@MarkCase.skipif(
    PlatformValue != "win32", reason="the positive fixture is scheduled on Windows"
)
def TestEqWin() -> None:
    RuntimePath = Environment.get("KIT_MEASURED_PART_PYTHON")
    if not RuntimePath:
        SkipCase("the measured runtime is supplied by the selected Windows shard")
    Report, Digest = RunEqCase(RuntimePath)
    assert Report["sha256"] == Digest
    assert Report["published_routes"] == 4
    AssertEqRead(Report, Digest)
