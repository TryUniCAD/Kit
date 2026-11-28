from dataclasses import replace as ReplaceValue
from math import tan as Tangent

from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfPlan import (
    ChmfEdgePlan,
    ChmfPlan,
    KStockBounds,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectBlind import (
    ProjectBlind,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadRectSketch import (
    ReadRectSketch,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from convert.adapters.solidworks.Core.Preparation.Chamfers.ReadChmfPicks import (
    ReadChmfPicks,
)
from convert.adapters.solidworks.Core.Preparation.Chamfers.ReadChmfValues import (
    ReadChmfValues,
)
from convert.adapters.solidworks.Core.Preparation.PartCaps import KPartWriteCaps
from interchange.Enums.EnumDocument import Capability
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentValidate import AssertValid
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter
from interchange.geometry.Models.Selection import Selection


# opposing authored limits determine the same center and width construction independently of saved coordinates
def ChmfInterval(Coordinates: tuple[float, ...]) -> tuple[tuple[float, float], float]:
    Lower, Upper = min(Coordinates), max(Coordinates)
    Center = (Lower / 2 + Upper / 2) / 1000.0
    SpanValue = (Upper - Lower) / 1000.0
    return (Center - SpanValue / 2, Center + SpanValue / 2), SpanValue


# only ordinary stock and one directly owned edge modification may reach native writing
def CheckChmfDoc(DocumentValue: CadDocument) -> None:
    CheckPlainScope(DocumentValue)
    AssertValid(DocumentValue)
    if (
        DocumentValue.units != "mm"
        or DocumentValue.assembly is not None
        or DocumentValue.DrawingValue is not None
        or DocumentValue.brep is not None
        or DocumentValue.meshes
        or DocumentValue.brep_payloads
        or DocumentValue.materials
        or not DocumentValue.capabilities <= KPartWriteCaps | {Capability.KSelections}
        or len(DocumentValue.feature_timeline) != 2
        or len(DocumentValue.parameters) not in (2, 3)
        or len(DocumentValue.bodies) != 1
        or len(DocumentValue.sketches) != 1
        or len(DocumentValue.selections) != 2
    ):
        raise ValueError(
            "chamfer requires the ordinary rectangular boss and exactly two physical picks"
        )


# the explicit operation order determines the controls regardless of portable inventory order
def ReadChmfParams(
    DocumentValue: CadDocument,
    BossValue: FeatureStep,
    ChmfValue: FeatureStep,
) -> tuple[Parameter, tuple[Parameter, ...]]:
    DriverIds = (*BossValue.parameter_ids, *ChmfValue.parameter_ids)
    Parameters = {Value.id: Value for Value in DocumentValue.parameters}
    if (
        len(BossValue.parameter_ids) != 1
        or len(ChmfValue.parameter_ids) not in (1, 2)
        or set(DriverIds) != set(Parameters)
        or len(set(DriverIds)) != len(DriverIds)
    ):
        raise ValueError(
            "chamfer requires distinct driving dimensions on the actual operations"
        )
    StockId, *ChamferIds = DriverIds
    return Parameters[StockId], tuple(Parameters[Value] for Value in ChamferIds)


# the actual step orders the two physical picks even if portable inventories are reordered
def FindChmfPicks(
    DocumentValue: CadDocument,
    ChmfValue: FeatureStep,
) -> tuple[Selection, Selection]:
    Selections = {Value.id: Value for Value in DocumentValue.selections}
    if len(ChmfValue.selection_ids) != 2 or set(ChmfValue.selection_ids) != set(
        Selections
    ):
        raise ValueError("chamfer requires exactly its two ordered physical picks")
    EdgeId, FaceId = ChmfValue.selection_ids
    return Selections[EdgeId], Selections[FaceId]


# full rectangle extents use the original modeled stations and millimetre depth
def ChmfStockBounds(
    DocumentValue: CadDocument,
    StockDim: Parameter,
) -> tuple[KStockBounds, float]:
    Points = ReadRectSketch(DocumentValue.sketches[0], 1.0)
    XValues, YValues = zip(*Points, strict=True)
    XBounds, Width = ChmfInterval(XValues)
    YBounds, Height = ChmfInterval(YValues)
    Depth = RequireScalar(StockDim.value.value) / 1000.0
    return (XBounds, YBounds, (0.0, Depth)), min(Width, Height, Depth)


# the scoped operation resolves the selected edge and offset side before creating any archive node
def PlanChmfPart(
    DocumentValue: CadDocument, *, AllowDistancePair: bool = False
) -> ChmfPlan:
    CheckChmfDoc(DocumentValue)
    BossValue, ChmfValue = DocumentValue.feature_timeline
    StockDim, Drivers = ReadChmfParams(DocumentValue, BossValue, ChmfValue)
    (BodyValue,) = DocumentValue.bodies
    EdgePick, FacePick = FindChmfPicks(DocumentValue, ChmfValue)
    if BodyValue.final_feature_id != ChmfValue.id or StockDim.value.unit != "mm":
        raise ValueError(
            "chamfer needs ordered edge and distance face picks and its actual result body"
        )
    StockDoc = ReplaceValue(
        DocumentValue,
        parameters=(StockDim,),
        selections=(),
        feature_timeline=(BossValue,),
        bodies=(ReplaceValue(BodyValue, final_feature_id=BossValue.id),),
    )
    StockValue = ProjectBlind(StockDoc, ReadRectSketch)
    if StockValue.PlaneName != "Front Plane" or StockValue.ConfigName != "Default":
        raise ValueError(
            "chamfer requires the ordinary Front Plane and Default configuration"
        )
    NameValue, Setback, Angle, Other = ReadChmfValues(
        ChmfValue, BossValue, Drivers, AllowDistancePair
    )
    BoundsValue, ShortSpan = ChmfStockBounds(DocumentValue, StockDim)
    EdgeValue = ReadChmfPicks(BoundsValue, ShortSpan, BossValue, (EdgePick, FacePick))
    SecondLeg = Setback * Tangent(Angle) if Angle is not None else Other or Setback
    CheckChmfLegs(EdgeValue, Setback, SecondLeg)
    return ChmfPlan(StockValue, EdgeValue, NameValue, Setback, Angle, Other)


# both independently measured face setbacks must end strictly inside the real stock
def CheckChmfLegs(EdgeValue: ChmfEdgePlan, Setback: float, OtherSetback: float) -> None:
    First = EdgeValue.DistanceAxis
    Other = next(
        Index for Index in range(3) if Index not in (First, EdgeValue.EdgeAxis)
    )
    AFloor, ACeil = EdgeValue.BoundsValue[First]
    BFloor, BCeil = EdgeValue.BoundsValue[Other]
    if (
        not 0.0 < Setback < ACeil - AFloor
        or not 0.0 < OtherSetback < BCeil - BFloor
    ):
        raise ValueError("chamfer setback would leave its actual incident stock faces")
