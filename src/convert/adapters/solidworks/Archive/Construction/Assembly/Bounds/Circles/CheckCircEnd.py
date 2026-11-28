from convert.adapters.solidworks.Archive.Construction.Blind.MakeEndSpec import (
    MakeEndSpec,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.Circles.CheckCircDims import (
    CheckCircDims,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireNode


# forward child depth must remain the actual live end and driving value rather than an independent stale neutral extent
def CheckCircEnd(ChildValue: PartCandidate, PlanValue: CirclePlan) -> None:
    CheckCircDims(ChildValue)
    BossValue = ChildValue.BossValue
    EndValue = RequireNode(BossValue.EndValue, "moEndSpec_c")
    FromValue = RequireNode(EndValue.FieldsValue.get("f140"), "moFromEndSpec_c")
    Forward, Reverse, DraftOne, DraftTwo = BossValue.DimensionsValue
    Parameter = RequireNode(Forward.ParameterValue, "moLengthParameter_c")
    Expected = MakeEndSpec(
        "blind",
        False,
        Forward.DisplayValue,
        Reverse.DisplayValue,
        DraftOne.DisplayValue,
        DraftTwo.DisplayValue,
        FromValue,
    )
    if (
        BossValue.FeatureValue.FieldsValue.get("f818") is not EndValue
        or EndValue.FieldsValue != Expected.FieldsValue
        or FromValue.FieldsValue != {"t": 0, "f28": BossValue.FromValue.DisplayValue}
        or Parameter.FieldsValue.get("f58") != PlanValue.DepthValue
    ):
        raise ValueError("circle bounds disagree with actual forward blind ownership")
