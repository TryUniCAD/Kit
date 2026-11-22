from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Feature.MakeThinDimMut import (
    MakeThinDimMut,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ThinWallPlan import (
    ThinWallPlan,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# radial endpoints depend on the modeled wall directions and actual axial midpoint
def GetWallSpans(
    PlanValue: RevolvePlan, WallValue: ThinWallPlan
) -> tuple[tuple[float, float, float], tuple[float, float, float] | None]:
    (Radial, Lower), (_, Upper) = PlanValue.VerticesValue
    Axial = (Lower + Upper) / 2
    First, Second = WallValue.LengthValues
    if WallValue.ModeValue == 2:
        return (Radial - First / 2, Radial + First / 2, Axial), None
    if WallValue.ModeValue == 1:
        return (Radial, Radial - First, Axial), None
    FirstSpan = (Radial, Radial + First, Axial)
    SecondSpan = (Radial, Radial - Second, Axial) if WallValue.ModeValue == 3 else None
    return FirstSpan, SecondSpan


# the cold native thin spec includes the measured inactive second display and end initializer state
def MakeThinSpecMut(
    FeatureValue: ArchiveNode,
    InputValue: PartBuildInput,
    Allocator: PersistentIds,
    SupportValue: PlaneFrame,
    PlanValue: RevolvePlan,
    WallValue: ThinWallPlan,
) -> ArchiveNode:
    First, Second = (
        MakeThinDimMut(
            FeatureValue,
            InputValue,
            Allocator,
            SupportValue,
            NameValue,
            LengthValue,
            SpanValue,
        )
        for NameValue, LengthValue, SpanValue in zip(
            ("D3", "D4"),
            WallValue.LengthValues,
            GetWallSpans(PlanValue, WallValue),
            strict=True,
        )
    )
    return ArchiveNode(
        RuntimeClass("moThinSpec_c", 1),
        {
            "f08": First,
            "f10": Second,
            "f2c": 0,
            "f30": -2.0,
            "f38": -2.0,
            "f28": WallValue.ModeValue,
            "f40": 1,
            "f48": None,
            "f50": 0,
            "f54": 0,
        },
    )
