from dataclasses import dataclass as DataClass
from math import dist as Distance
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfPlan import ChmfPlan
from convert.adapters.solidworks.Archive.Construction.Chamfers.Views.PickChmfView import (
    PickChmfView,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumOffset,
    KDatumVector,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.CrossVector import (
    CrossVector,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    AnnoViewInput,
)

# ordinary neutral chamfer dimensions have one generated local view shared by their displays
KChmfViewName = "Chamfer Driver View"


# both dimensions share the actual edge center and the setback anchor in its incident basis
@DataClass(frozen=True, slots=True)
class ChmfFrame:
    FrameValue: PlaneFrame
    EdgeCenter: KDatumVector
    ViewInput: AnnoViewInput
    SenseValue: float

    # inverse projection belongs to the named display view while world witnesses stay in the stock frame
    @property
    def ViewFrame(self) -> PlaneFrame:
        return PlaneFrame(self.FrameValue.OriginValue, *self.ViewInput.BasisValue)


# the selected signed carrier supplies its outward normal and the positive setback orientation
def MakeChmfFrame(PlanValue: ChmfPlan, NameValue: str = KChmfViewName) -> ChmfFrame:
    EdgeValue = PlanValue.EdgeValue
    First = EdgeValue.DistanceAxis
    Along = EdgeValue.EdgeAxis
    Other = next(Index for Index in range(3) if Index not in (First, Along))
    CornerBits = EdgeValue.CornerBits
    Center = CastValue(
        KDatumVector,
        tuple(
            (
                Lower / 2 + Upper / 2
                if Index == Along
                else (Lower, Upper)[CornerBits[Index]]
            )
            for Index, (Lower, Upper) in enumerate(EdgeValue.BoundsValue)
        ),
    )
    AxisU = CastValue(
        KDatumVector,
        tuple(
            float(2 * CornerBits[First] - 1) if Index == First else 0.0
            for Index in range(3)
        ),
    )
    AxisV = CastValue(
        KDatumVector,
        tuple(
            float(2 * CornerBits[Other] - 1) if Index == Other else 0.0
            for Index in range(3)
        ),
    )
    return BindChmfFrame(PlanValue, Center, AxisU, AxisV, NameValue)


# the construction anchor and optional display basis are separately derived and validated
def BindChmfFrame(
    PlanValue: ChmfPlan,
    Center: KDatumVector,
    AxisU: KDatumVector,
    AxisV: KDatumVector,
    NameValue: str,
) -> ChmfFrame:
    Normal = CrossVector(AxisU, AxisV)
    Anchor = DatumOffset(Center, AxisU, -PlanValue.SetbackValue)
    if (
        Anchor == Center
        or abs(Distance(Anchor, Center) - PlanValue.SetbackValue) > 1e-12
    ):
        raise ValueError(
            "chamfer display anchor must retain the modeled setback distance"
        )
    StockBasis = AxisU, AxisV, Normal
    IntentValue = PlanValue.DisplayValue
    ViewValue, Sense = (
        (AnnoViewInput(NameValue, StockBasis), 1.0)
        if IntentValue is None
        else PickChmfView(IntentValue, StockBasis)
    )
    return ChmfFrame(PlaneFrame(Anchor, *StockBasis), Center, ViewValue, Sense)
