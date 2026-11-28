from itertools import permutations as Permutations
from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Construction.AssemblySets.MakeOrderCase import (
    MakeOrderCase,
)
from tests.Convert.Solidworks.Research.Construction.AssemblySets.RunOrderPhase import (
    RunOrderPhase,
)


# every permutation of the three supported mate families must preserve complete actual graph publication across two unrelated plain child and rigid placement variants
def TestOrderFlow() -> None:
    for KindOrder in Permutations(("coincident", "parallel", "distance")):
        for IsVariant in (False, True):
            Request = MakeOrderCase(KindOrder, IsVariant)
            BuiltValue = RunOrderPhase(Request, "build")
            Projected: dict[str, object] = {"request": Request, "build": BuiltValue}
            Prepared = RunOrderPhase(Projected, "prepare")
            Compared = RunOrderPhase(Projected, "counterpart")
            assert Prepared["round_trips"] == 22
            assert Compared["same_as_independent_research"] is True
            assert BuiltValue["wrapper_next_id"] == 6
            MateIds = CastValue(list[int], BuiltValue["mate_ids"])
            DimensionIds = CastValue(list[int], BuiltValue["dimension_ids"])
            assert len(set(MateIds)) == 3 and len(DimensionIds) == 1
            assert DimensionIds[0] < MateIds[KindOrder.index("distance")]
