from pathlib import Path as FilePath
from typing import cast as CastValue

from interchange import CadDocument
from tests.Convert.Solidworks.Research.Assembly.TypedMates.RunMateRead import (
    RunMateRead,
)
from tests.Convert.Solidworks.Research.Assembly.TypedMates.SaveFixedPair import (
    SaveFixedPair,
)
from tests.Convert.Solidworks.Research.Construction.AssemblySets.MakeOrderCase import (
    MakeOrderCase,
)
from tests.Convert.Solidworks.Research.Construction.AssemblySets.RunOrderPhase import (
    RunOrderPhase,
)


# either authored anchor must survive complete file generation and strict public component resolution without changing deferred legacy admission
def TestFixedFlags(TmpPath: FilePath) -> None:
    for FixedIndex in (0, 1):
        Request = MakeOrderCase(
            ("coincident", "distance", "parallel"), bool(FixedIndex)
        )
        for MateValue in CastValue(list[dict[str, object]], Request["mates"]):
            MateValue["fixed_occurrence"] = FixedIndex
        BuiltValue = RunOrderPhase(Request, "build")
        ParentPath = SaveFixedPair(Request, BuiltValue, TmpPath / str(FixedIndex))
        Outcome = RunMateRead(ParentPath)
        assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
        Document = CadDocument.from_json(Outcome.stdout)
        Document.assert_valid()
        Assembly = Document.assembly
        assert Assembly is not None
        Occurrences = CastValue(list[dict[str, object]], Request["occurrences"])
        ByName = {ItemValue.name: ItemValue for ItemValue in Assembly.instances}
        assert tuple(
            ByName[CastValue(str, Value["name"])].fixed for Value in Occurrences
        ) == tuple(IndexValue == FixedIndex for IndexValue in range(2))
        assert len(Assembly.mates) == 3 and len(Assembly.mate_entities) == 6
        Deferred = RunMateRead(ParentPath, AdapterValues={"resolve_components": False})
        assert Deferred.returncode != 0 and "has no entities" in Deferred.stderr
