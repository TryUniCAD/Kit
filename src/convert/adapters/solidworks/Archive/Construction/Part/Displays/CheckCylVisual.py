from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PartLookInput import (
    PartLookInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)


# the measured radial holder belongs to an ordinary forward front child with a named renderer
def CheckCylVisual(PlanValue: CirclePlan, RenderValue: PartLookInput | None) -> None:
    if (
        type(RenderValue) is not PartLookInput
        or PlanValue.AxisValue != "z"
        or PlanValue.PlaneName != "Front Plane"
        or PlanValue.ConfigName != "Default"
        or PlanValue.IsDiameter
        or PlanValue.EndValue.ModeValue != "blind"
        or PlanValue.EndValue.IsReversed
    ):
        raise ValueError(
            "concentric child appearance requires an ordinary Front radial blind boss"
        )
