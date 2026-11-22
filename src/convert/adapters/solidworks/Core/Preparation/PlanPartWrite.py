from math import isfinite as IsFinite

from convert.Geometry.Extrude.Polygon.PrismRing import CheckSimpleRing, MeasureRing
from convert.Geometry.Extrude.Polygon.RingPredicates import ToRingGrid
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectBlind import (
    ProjectBlind,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLineLoop import (
    ReadLineLoop,
)
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from convert.adapters.solidworks.Core.Preparation.PartCaps import KPartWriteCaps
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.VectorPlane import PlaneVector


# the ordinary native profile must admit only the proven millimetre line loop and front support semantics
def PlanPartWrite(DocumentValue: CadDocument) -> BlindPlan:
    CheckPlainScope(DocumentValue)
    if not DocumentValue.capabilities <= KPartWriteCaps:
        raise ValueError("native part preparation has unrepresented capabilities")
    PlanValue = ProjectBlind(DocumentValue, ReadLineLoop)
    if DocumentValue.units != "mm" or PlanValue.PlaneName != "Front Plane":
        raise ValueError("native part preparation requires millimetres and Front Plane")
    MetrePoints = tuple(PlaneVector(*PointValue) for PointValue in PlanValue.VerticesValue)
    ExactPoints, _ = ToRingGrid(MetrePoints)
    CheckSimpleRing(ExactPoints)
    _, AreaValue, Perimeter = MeasureRing(
        tuple(
            PlaneVector(XCoord * 1000.0, YCoord * 1000.0)
            for XCoord, YCoord in PlanValue.VerticesValue
        )
    )
    HeightValue = PlanValue.DepthValue * 1000.0
    VolumeValue = AreaValue * HeightValue
    if not (
        IsFinite(VolumeValue)
        and VolumeValue > 0
        and IsFinite(2 * AreaValue + Perimeter * HeightValue)
    ):
        raise ValueError("native part measures exceed the readable prism domain")
    return PlanValue
