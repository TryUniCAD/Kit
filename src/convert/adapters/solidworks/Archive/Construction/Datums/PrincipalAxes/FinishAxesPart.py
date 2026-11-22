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
        or PlanValue.AxisValue != "y"
        or not PlanValue.Reversed
        or len(SketchDims) != 2
        or len(SystemValue.ConfigValues) != 1
        or SystemValue.ManagerValue.FieldsValue.get("f360")
        is not StockValue.CurrentConfig
    ):
        raise ValueError(
            "principal axis construction requires its actual dimensioned signed stock"
        )
    PutAxisViewsMut(
        SystemValue, (PlanValue.WidthValue, PlanValue.DepthValue, PlanValue.HeightValue)
    )
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
