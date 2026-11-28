from sys import executable as PythonExec

from tests.Convert.Solidworks.WidthDepth.AssertEqRead import AssertEqRead
from tests.Convert.Solidworks.WidthDepth.RunEqCase import RunEqCase


# an independently authored queue request verifies the real strict reader and gated writer in a fresh process
def TestMeasuredEq() -> None:
    Report, Digest = RunEqCase(PythonExec)
    AssertEqRead(Report, Digest)
