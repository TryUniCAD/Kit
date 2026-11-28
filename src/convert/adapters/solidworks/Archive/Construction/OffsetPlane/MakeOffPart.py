from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import (
    FrameXform,
)
from convert.adapters.solidworks.Archive.Construction.Circles.AddCircDimMut import (
    AddCircDimMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.InitOffListsMut import (
    InitOffListsMut,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.MakeOffCircMut import (
    MakeOffCircMut,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.MakeOffsetMut import (
    MakeOffsetMut,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffsetInput import (
    OffsetInput,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffBaseFrame import (
    OffBaseFrame,
)
from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import (
    FinishBlindMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import (
    MakePartBaseMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import (
    MakeSketchKeys,
)


# ordinary offset parts share the actual ordered system plane sketch and blind boss construction
def MakeOffPart(
    PlanValue: CirclePlan, DatumInput: OffsetInput, InputValue: PartBuildInput
) -> PartCandidate:
    System = InputValue.SystemValue
    if (
        PlanValue.IsDiameter
        or PlanValue.EndValue.IsReversed
        or PlanValue.EndValue.ModeValue != "blind"
        or System.OriginAxis != PlanValue.AxisValue
        or dict(System.PlaneNames).get(PlanValue.AxisValue) != PlanValue.PlaneName
        or DatumInput.NameValue
        in (
            *(NameValue for _, NameValue in System.FolderValues + System.PlaneNames),
            System.OriginName,
            System.CabinetName,
            PlanValue.NameValue,
            PlanValue.SketchName,
            PlanValue.FeatureName,
        )
    ):
        raise ValueError(
            "offset part requires distinct names and its centred radius driven blind profile"
        )
    Allocator = PersistentIds()
    SystemValue = MakePartBaseMut(InputValue, PlanValue, Allocator)
    InitOffListsMut(SystemValue.RootValue)
    SystemValue.OriginValue.ProfileValue.FieldsValue["pd_ff0"] = FrameXform(
        OffBaseFrame(PlanValue.AxisValue)
    )
    OffsetValue = MakeOffsetMut(
        DatumInput,
        SystemValue.SystemValues.PlaneValues[PlanValue.AxisValue],
        PlanValue.AxisValue,
        SystemValue.RootValue,
        InputValue.TargetValue,
        Allocator,
        InputValue.DesignIntent,
        InputValue.SelectedLeader,
    )
    ProfileValue = MakeOffCircMut(
        PlanValue.SketchName,
        PlanValue.CircleValue,
        SystemValue.RootValue,
        OffsetValue,
        InputValue.TargetValue,
        Allocator,
    )
    Driver = AddCircDimMut(
        ProfileValue,
        PlanValue.TextPoint,
        False,
        InputValue.DesignIntent,
        InputValue.SelectedLeader,
        Allocator,
        OffsetValue=OffsetValue,
    )
    return FinishBlindMut(
        ReplaceValue(
            SystemValue,
            FeatureValues=(*SystemValue.FeatureValues, OffsetValue.FeatureValue),
        ),
        ProfileValue,
        InputValue,
        PlanValue,
        Allocator,
        MakeSketchKeys((Driver,), InputValue.DocumentUnits.LengthUnit),
        OffsetValue=OffsetValue,
    )
