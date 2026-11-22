from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfFrame import (
    ChmfFrame,
    MakeChmfFrame,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfPlan import ChmfPlan
from convert.adapters.solidworks.Archive.Construction.Chamfers.MakeChmfAngle import (
    MakeChmfAngle,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.MakeChmfDist import (
    MakeChmfDist,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.PutAnnoCatalog import (
    PutAnnoCatalog,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# the second setback uses the other incident carrier and a distinct signed display frame
def MakeOtherPlan(PlanValue: ChmfPlan, SetbackValue: float) -> ChmfPlan:
    EdgeValue = PlanValue.EdgeValue
    OtherAxis = 3 - EdgeValue.EdgeAxis - EdgeValue.DistanceAxis
    return ReplaceValue(
        PlanValue,
        EdgeValue=ReplaceValue(EdgeValue, DistanceAxis=OtherAxis),
        SetbackValue=SetbackValue,
        OtherSetback=None,
    )


# the active mode decides which live driver chains the feature owns
def MakeChmfDrivers(
    ModelValue: ArchiveNode, Feature: ArchiveNode, PlanValue: ChmfPlan
) -> tuple[tuple[str, DimensionGraph], ...]:
    BasisValue = MakeChmfFrame(PlanValue)
    OtherSetback = PlanValue.OtherSetback
    OtherInput: tuple[ChmfPlan, ChmfFrame] | None = None
    if OtherSetback is not None:
        OtherPlan = MakeOtherPlan(PlanValue, OtherSetback)
        OtherBasis = MakeChmfFrame(OtherPlan, "Chamfer Second Driver View")
        OtherInput = OtherPlan, OtherBasis
    Inputs = (
        (BasisValue.ViewInput,)
        if OtherInput is None
        else (BasisValue.ViewInput, OtherInput[1].ViewInput)
    )
    Views = PutAnnoCatalog(ModelValue, 19000, Inputs, None, (None,))
    ViewId = FieldInt(Views[BasisValue.ViewInput.NameValue].FieldsValue, "f360")
    Distance = ("f810", MakeChmfDist(Feature, PlanValue, BasisValue, ViewId))
    if PlanValue.AngleValue is not None:
        return Distance, ("f818", MakeChmfAngle(Feature, PlanValue, BasisValue, ViewId))
    if OtherInput is None:
        return (Distance,)
    OtherPlan, OtherBasis = OtherInput
    OtherId = FieldInt(Views[OtherBasis.ViewInput.NameValue].FieldsValue, "f360")
    Other = MakeChmfDist(Feature, OtherPlan, OtherBasis, OtherId, "D3")
    return Distance, ("f820", Other)
