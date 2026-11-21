from tests.Convert.Solidworks.Research.Drawing.SdkLinked.AssertLinked import (
    AssertLinked,
)
from tests.Convert.Solidworks.Research.Drawing.SdkLinked.MakeLinkedJob import (
    MakeLinkedJob,
)
from tests.Convert.Solidworks.Research.Drawing.SdkLinked.RunLinkedCase import (
    RunLinkedCase,
)


# separate generated children and named view profiles must preserve complete file bytes and independently projected prism geometry
def TestSdkLinked() -> None:
    HashesValue: set[object] = set()
    for Label, WidthValue, HeightValue, DepthValue, Orientation, ScaleValue in (
        ("LinkedFrontAlpha", 37.9, 22.7, 14.3, "*Front", 1.0),
        ("LinkedFrontBetaΩ", 19.3, 31.7, 9.1, "*Front", 0.625),
        ("LinkedTop", 41.3, 18.9, 7.7, "*Top", 1.375),
        ("LinkedRight", 18.7, 29.1, 13.9, "*Right", 0.875),
        ("LinkedIsometric", 29.3, 17.9, 21.1, "*Isometric", 0.7),
        ("LinkedNearUnity", 15.7, 13.1, 8.9, "*Front", 1.000000005),
    ):
        JobValue = MakeLinkedJob(
            Label, WidthValue, HeightValue, DepthValue, Orientation, ScaleValue
        )
        Result = RunLinkedCase(JobValue)
        assert Result == RunLinkedCase(JobValue)
        Counterpart = RunLinkedCase({"request": JobValue, "build": Result}, True)
        AssertLinked(Result, Counterpart)
        HashesValue.add(Result["artifact_sha256"])
    assert len(HashesValue) == 6
