from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Assembly.Combined.AddThirdMate import (
    AddThirdMate,
)
from tests.Convert.Solidworks.Research.Assembly.Combined.MakeCombinedCase import (
    MakeCombinedCase,
)
from tests.Convert.Solidworks.Research.Assembly.Combined.RunCombinedCase import (
    RunCombinedCase,
)


# native bundle streams must retain registration order and grow with actual authored mates
def TestCombinedMates() -> None:
    Pair = MakeCombinedCase(False)
    Triple = MakeCombinedCase(True)
    AddThirdMate(Triple)
    Lengths: list[int] = []
    for Count, Request in ((2, Pair), (3, Triple)):
        Report = RunCombinedCase(Request)
        assert Report == RunCombinedCase(Request)
        Inspection = CastValue(dict[str, object], Report["inspection"])
        assert Report["input_runtime_file_access_attempts"] == 0
        assert Inspection["next_wrapper_id"] == Count * 2
        assert Inspection["mate_count"] == Inspection["occurrence_count"] == Count
        assert len(CastValue(list[str], Inspection["logical_round_trips"])) == 7
        Lengths.append(CastValue(int, Inspection["length"]))
    assert Lengths[0] < Lengths[1]


# conflicting authored names or fixed anchors must fail before a native bundle is published
def TestRejectCombinedMates() -> None:
    Request = MakeCombinedCase(False)
    Bundle = CastValue(dict[str, object], Request["bundle"])
    First, Second = CastValue(list[dict[str, object]], Bundle["mates"])
    OriginalName = Second["name"]
    Second["name"] = First["name"]
    _ = RunCombinedCase(Request, "distinct nonempty names")
    Second["name"] = OriginalName
    Second["fixed_occurrence"] = 0
    _ = RunCombinedCase(Request, "one shared fixed occurrence")
