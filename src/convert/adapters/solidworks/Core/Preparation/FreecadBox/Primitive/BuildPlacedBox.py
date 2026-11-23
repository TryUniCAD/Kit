from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import (
    FrameXform,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.InitOffListsMut import (
    InitOffListsMut,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.MakeOffPolyMut import (
    MakeOffPolyMut,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.MakeOffsetMut import (
    MakeOffsetMut,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffBaseFrame import (
    OffBaseFrame,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffsetGraph import (
    OffsetGraph,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffsetInput import (
    OffsetInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import (
    CheckPartInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import (
    FinishBlindMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import (
    MakePartBaseMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import (
    MakePartProfMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import (
    ProjectRectDims,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonInput import (
    PolygonInput,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeRectDimsMut import (
    MakeRectDimsMut,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import (
    MakeSketchKeys,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.FreecadBox.BoxAnchorInput import (
    BoxAnchorInput,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Primitive.BindStockFix import (
    BindStockFix,
)
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.RequirePartPath import RequirePartPath
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Transform import KTransformIdentity


# the nonzero normal component has its own measured class and signed distance driver
def MakeDatumMut(
    SystemValue: PartSystem,
    InputValue: PartBuildInput,
    PlanValue: BlindPlan,
    Allocator: PersistentIds,
    DatumName: str,
    ZValue: float,
) -> OffsetGraph:
    InitOffListsMut(SystemValue.RootValue)
    SystemValue.OriginValue.ProfileValue.FieldsValue["pd_ff0"] = FrameXform(
        OffBaseFrame(PlanValue.AxisValue)
    )
    return MakeOffsetMut(
        OffsetInput(DatumName, abs(ZValue), ZValue < 0, 19000),
        SystemValue.SystemValues.PlaneValues[PlanValue.AxisValue],
        PlanValue.AxisValue,
        SystemValue.RootValue,
        InputValue.TargetValue,
        Allocator,
        InputValue.DesignIntent,
        InputValue.SelectedLeader,
    )


# target placement keeps true planar coordinates and depth in their independent native owners
def BuildPlacedBox(
    Document: CadDocument, PathValue: str, WrittenAt: int
) -> PartCandidate:
    (PlaneValue,) = Document.support_planes
    PoseValue = PlaneValue.transform
    if ReplaceValue(PoseValue, origin=KTransformIdentity.origin) != KTransformIdentity:
        raise ValueError("placed stock requires a translation without rigid rotation")
    XValue, YValue, ZValue = (
        NumberValue * 0.001
        for NumberValue in (PoseValue.origin.x, PoseValue.origin.y, PoseValue.origin.z)
    )
    Principal = ReplaceValue(
        Document,
        support_planes=(ReplaceValue(PlaneValue, transform=KTransformIdentity),),
    )
    PlanValue = ProjectRectDims(Principal)
    PlanValue = ReplaceValue(
        PlanValue,
        VerticesValue=tuple(
            (First + XValue, Second + YValue)
            for First, Second in PlanValue.VerticesValue
        ),
    )
    Output = RequirePartPath(PathValue, WrittenAt)
    Recipe = MakePartRecipe(PlanValue, WrittenAt)
    InputValue = BindPartIntent(Principal, PlanValue, Recipe, Output)
    DatumName = PlanValue.FeatureName + " Placement"
    CheckPartInput(Principal, InputValue, PlanValue, (DatumName,) if ZValue else ())
    Allocator = PersistentIds()
    System = MakePartBaseMut(InputValue, PlanValue, Allocator)
    OffsetValue = None
    if ZValue:
        OffsetValue = MakeDatumMut(
            System, InputValue, PlanValue, Allocator, DatumName, ZValue
        )
        Profile = MakeOffPolyMut(
            PlanValue.SketchName,
            PolygonInput(PlanValue.VerticesValue, 19000),
            System.RootValue,
            OffsetValue,
            InputValue.TargetValue,
            Allocator,
        )
        System = ReplaceValue(
            System, FeatureValues=(*System.FeatureValues, OffsetValue.FeatureValue)
        )
    else:
        Profile = MakePartProfMut(System, InputValue, PlanValue, Allocator)
    DimPlace = BoxAnchorInput(PlanValue, False).DimensionsValue
    DimPlace = ReplaceValue(
        DimPlace,
        WidthText=(DimPlace.WidthText[0] + XValue, DimPlace.WidthText[1] + YValue),
        HeightText=(DimPlace.HeightText[0] + XValue, DimPlace.HeightText[1] + YValue),
    )
    Drivers = MakeRectDimsMut(
        Profile,
        DimPlace,
        Allocator,
        PlanValue.SketchDriverNames,
        OffsetValue=OffsetValue,
    )
    BindStockFix(Profile)
    return FinishBlindMut(
        System,
        Profile,
        InputValue,
        PlanValue,
        Allocator,
        MakeSketchKeys(Drivers, InputValue.DocumentUnits.LengthUnit),
        OffsetValue=OffsetValue,
    )
