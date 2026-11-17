from pathlib import Path as FilePath
from typing import cast as CastValue

from interchange import CadDocument
from tests.Convert.Solidworks.Research.Assembly.PlanarMateInput import MakeMateInput
from tests.Convert.Solidworks.Research.Assembly.RunMateBundle import RunMateBundle
from tests.Convert.Solidworks.Research.Assembly.TypedMates.AssertPublicMate import (
    AssertPublic,
)
from tests.Convert.Solidworks.Research.Assembly.TypedMates.RunMateFaults import (
    RunMateFaults,
)
from tests.Convert.Solidworks.Research.Assembly.TypedMates.RunMateRead import (
    RunMateRead,
)


# corrupted graph references caches and child identities must never become successful public mate rules
def TestMateRejects(TmpPath: FilePath) -> None:
    ParentPath, ChildPath = RunMateBundle(
        MakeMateInput("publicreject"), TmpPath / "pair"
    )
    _, WrongChild = RunMateBundle(MakeMateInput("different"), TmpPath / "other")
    CasesValue = RunMateFaults(ParentPath, ChildPath, WrongChild, TmpPath / "faults")
    for CaseValue in CasesValue:
        Outcome = RunMateRead(FilePath(CastValue(str, CaseValue["path"])))
        assert Outcome.returncode != 0, str(CaseValue["case"])
        assert "typed planar mate graph rejected:" in Outcome.stderr
        assert (
            CastValue(str, CaseValue["expected_error"]) in Outcome.stderr
        ), f"{CaseValue['case']}: {Outcome.stderr}"
    Control = RunMateRead(ParentPath)
    assert Control.returncode == 0, Control.stdout + Control.stderr
    AssertPublic(CadDocument.from_json(Control.stdout))
