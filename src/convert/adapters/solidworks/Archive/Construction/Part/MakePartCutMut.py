from convert.adapters.solidworks.Archive.Construction.Circles.AddCircDimMut import (
    AddCircDimMut,
)
from convert.adapters.solidworks.Archive.Construction.Circles.MakeCircleFeat import (
    MakeCircleFeat,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.CutGraph import CutGraph
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeBlindCutMut import (
    MakeBlindCutMut,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.PocketPlan import (
    PocketPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import (
    MakeSketchKeys,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)


# the actual cut profile uses the same front datum and allocation history as the earlier boss
def MakePartCutMut(
    SystemValue: PartSystem,
    InputValue: PartBuildInput,
    PlanValue: PocketPlan,
    Allocator: PersistentIds,
) -> tuple[CutGraph, tuple[KeywordDim, ...]]:
    ProfileValue = MakeCircleFeat(
        PlanValue.SketchName,
        SystemValue.RootValue,
        SystemValue.SystemValues.PlaneValues["z"],
        "z",
        PlanValue.CircleValue,
        InputValue.TargetValue,
        Allocator,
    )
    SketchDims: tuple[KeywordDim, ...] = ()
    if PlanValue.RadialMode is not None:
        CenterX, CenterY = PlanValue.CircleValue.CenterValue
        RadiusValue = PlanValue.CircleValue.RadiusValue
        RadialValue = AddCircDimMut(
            ProfileValue,
            (CenterX + RadiusValue * 2, CenterY + RadiusValue),
            PlanValue.RadialMode == "diameter",
            InputValue.DesignIntent,
            InputValue.SelectedLeader,
            Allocator,
        )
        SketchDims = MakeSketchKeys((RadialValue,), InputValue.DocumentUnits.LengthUnit)
    CutValue = MakeBlindCutMut(
        PlanValue.FeatureName,
        SystemValue.RootValue,
        ProfileValue,
        PlanValue.EndValue,
        InputValue.TargetValue,
        Allocator,
        InputValue.DesignIntent,
        InputValue.SelectedLeader,
    )
    return CutValue, SketchDims
