from os import name as OsName

from pytest import mark as MarkCase

from tests.Convert.Solidworks.ImportWriting.CheckImportPath import CheckImportPath


# the native receipt binds the actual windows locator and requires physical staging evidence
@MarkCase.skipif(
    OsName != "nt", reason="the measured physical locator requires Windows"
)
def TestConcaveWin() -> None:
    CheckImportPath("ConcaveOwned", 10890)
