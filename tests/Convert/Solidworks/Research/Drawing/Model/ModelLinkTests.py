from tests.Convert.Solidworks.Research.Drawing.Linked.MakeFrontJob import MakeFrontJob
from tests.Convert.Solidworks.Research.Drawing.Model.AssertModel import AssertModel
from tests.Convert.Solidworks.Research.Drawing.Model.MakeModelInput import (
    MakeModelInput,
)
from tests.Convert.Solidworks.Research.Drawing.Model.RunModelCase import RunModelCase


# generated drawing self ownership must remain valid when an ordinary external child and both view support pairs attach
def TestModelLinks() -> None:
    for Label, Width, Height, Depth in (
        ("ModelLinkedAlpha", 0.0353, 0.0279, 0.0127),
        ("ModelLinkedBeta", 0.0241, 0.0329, 0.0171),
    ):
        JobValue = MakeFrontJob(Label, Width, Height, Depth)
        Request = JobValue["request"]
        if not isinstance(Request, dict):
            raise TypeError("drawing root linked input must be a neutral request")
        Request["drawing"] = MakeModelInput(Label, 11, 3)
        JobValue.update(schema="kit.sw2026.sdk-drawing-model-process.v1", mode="front")
        Result = RunModelCase(JobValue)
        assert Result == RunModelCase(JobValue)
        AssertModel(Result, 172)
        assert Result["mode"] == "front"
