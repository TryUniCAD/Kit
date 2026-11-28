from tests.Convert.Solidworks.Research.Construction.Nesting.MakeNestedCase import (
    MakeNestedCase,
)
from tests.Convert.Solidworks.Research.Construction.Nesting.RunNestedPhase import (
    RunNestedPhase,
)


# shared subassembly definitions must generate deterministic complete files across different recursive topologies without reading native inputs
def TestNestedFlow() -> None:
    for IsMixed in (False, True):
        Request = MakeNestedCase(IsMixed, r"C:\KitSdkNested")
        FirstValue = RunNestedPhase(Request)
        SecondValue = RunNestedPhase(Request)
        FirstProcess = FirstValue.pop("worker_pid")
        SecondProcess = SecondValue.pop("worker_pid")
        assert FirstProcess != SecondProcess
        assert FirstValue == SecondValue
        assert FirstValue["definition_count"] == (4 if IsMixed else 3)
        assert FirstValue["expanded_root_occurrences"] == (7 if IsMixed else 2)
        assert FirstValue["typed_stream_round_trips"] == (44 if IsMixed else 34)
