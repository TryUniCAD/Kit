from pathlib import Path as FilePath

from interchange import CadDocument
from tests.Convert.Solidworks.Research.Assembly.PlanarMateInput import MakeMateInput
from tests.Convert.Solidworks.Research.Assembly.RunMateBundle import RunMateBundle
from tests.Convert.Solidworks.Research.Assembly.TypedMates.AssertPublicMate import (
    AssertPublic,
)
from tests.Convert.Solidworks.Research.Assembly.TypedMates.RunMateRead import (
    RunMateRead,
)


# neutral generation must produce usable public mate rules without optional saved selection strings
def TestPublicMates(TmpPath: FilePath) -> None:
    ParentPath, _ = RunMateBundle(MakeMateInput("publictyped"), TmpPath / "pair")
    Outcome = RunMateRead(ParentPath)
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    AssertPublic(CadDocument.from_json(Outcome.stdout))
    Deferred = RunMateRead(ParentPath, AdapterValues={"resolve_components": False})
    assert Deferred.returncode != 0 and "has no entities" in Deferred.stderr
