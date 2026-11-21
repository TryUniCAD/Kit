from tests.Convert.Solidworks.Research.Construction.PlanarGroups.GroupCaseInput import (
    GroupCaseInput,
)
from tests.Convert.Solidworks.Research.Construction.PlanarGroups.RunGroupPhase import (
    RunGroupPhase,
)


# both ends of the actual component list must support deterministic complete group publication with every explicit endpoint and dimension preserved across linked streams
def TestGroupFlows() -> None:
    ProcessIds: set[int] = set()
    for CountValue in (2, 3, 5):
        for IsVariant in (False, True):
            RequestValue = GroupCaseInput(CountValue, IsVariant)
            FirstValue = RunGroupPhase(RequestValue)
            SecondValue = RunGroupPhase(RequestValue)
            FirstId, SecondId = FirstValue.pop("worker_pid"), SecondValue.pop(
                "worker_pid"
            )
            assert type(FirstId) is int and type(SecondId) is int
            assert FirstId != SecondId
            ProcessIds.update((FirstId, SecondId))
            assert FirstValue == SecondValue
            assert FirstValue["occurrence_count"] == CountValue
            MateValues = CastValue(list[dict[str, object]], RequestValue["mates"])
            assert FirstValue["mate_count"] == len(MateValues)
            assert FirstValue["fixed_indices"] == [CountValue - 1 if IsVariant else 0]
            assert FirstValue["round_trips"] == 22
    assert len(ProcessIds) == 12


from typing import cast as CastValue
