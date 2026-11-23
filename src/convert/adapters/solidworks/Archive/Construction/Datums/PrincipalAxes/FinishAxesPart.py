from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
)
from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.EmitAxesPart import (
    EmitAxesPart,
)
from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.MakeAxesHeaders import (
    MakeAxesHeaders,
)
from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.MakePosAxisMut import (
    MakePosAxisMut,
)
from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.PrincipalAxes import (
    PrincipalAxes,
)
from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.PrincipalAxisBasis import (
    KAxisSupports,
)
from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.PutAxisViewsMut import (
    PutAxisViewsMut,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)


# actual stock corners fix which signed principal envelope supplies the axis displays
def ReadAxisStock(PlanValue: BlindPlan) -> tuple[KDatumVector, bool]:
    SignedTop = PlanValue.AxisValue == "y" and PlanValue.Reversed
    Front = PlanValue.AxisValue == "z" and not PlanValue.Reversed
    Width, Height, Depth = (
        PlanValue.WidthValue,
        PlanValue.HeightValue,
        PlanValue.DepthValue,
    )
    FarSide = -Height if SignedTop else Height
    if not (SignedTop or Front) or PlanValue.VerticesValue != (
        (0.0, 0.0),
        (Width, 0.0),
        (Width, FarSide),
        (0.0, FarSide),
    ):
        raise ValueError("principal axes require an origin anchored signed rectangle")
    return ((Width, Depth, Height) if SignedTop else (Width, Height, Depth)), SignedTop


# the complete principal datum graph shares the ordinary cold stock and its same live allocator
def FinishAxesPart(
    StockValue: PartCandidate,
    InputValue: PartBuildInput,
    Allocator: PersistentIds,
    AxesValue: PrincipalAxes,
    SketchDims: tuple[KeywordDim, ...],
) -> PartCandidate:
    SystemValue = StockValue.SystemValue
    PlanValue = StockValue.PlanValue
    if (
        type(PlanValue) is not BlindPlan
        or len(SketchDims) != 2
        or len(SystemValue.ConfigValues) != 1
        or SystemValue.ManagerValue.FieldsValue.get("f360")
        is not StockValue.CurrentConfig
    ):
        raise ValueError(
            "principal axis construction requires its actual dimensioned signed stock"
        )
    Spans, SignedTop = ReadAxisStock(PlanValue)
    PutAxisViewsMut(SystemValue, Spans, SignedTop=SignedTop)
    AxisNodes = tuple(
        MakePosAxisMut(
            SystemValue,
            InputValue,
            Allocator,
            (StockValue.HeaderValue, StockValue.TopHeader),
            AxisValue,
            Supports,
        )
        for AxisValue, Supports in zip(AxesValue.AxisValues, KAxisSupports, strict=True)
    )
    Headers = MakeAxesHeaders(SystemValue, InputValue, Allocator, AxisNodes)
    return EmitAxesPart(StockValue, InputValue, SketchDims, AxisNodes, Headers)
