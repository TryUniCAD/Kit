from collections.abc import Mapping
from math import dist as Distance

from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.FrontStockBox import (
    KStockBounds,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.CheckPatPick import (
    CheckPatPick,
)
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Features.FeaturePlaneAxis import PlaneAxis
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.PlaneExtAxis import GetExtVector
from interchange.geometry.Models.Selection import Selection


# the authored hinge must reproduce the directed finite first plane intersection
def CheckPatHinge(
    HingeValue: FeatureStep,
    TopId: str,
    RightId: str,
    PickValues: Mapping[str, Selection],
    BoundsValue: KStockBounds,
) -> None:
    Definition = HingeValue.definition
    if (
        type(Definition) is not PlaneAxis
        or HingeValue.kind is not FeatureKind.KReference
    ):
        raise ValueError("a typed finite plane intersection axis is required")
    if (
        HingeValue.parameter_ids
        or HingeValue.input_feature_ids
        or HingeValue.operation is not None
        or HingeValue.sketch_id is not None
        or HingeValue.selection_ids
        != (Definition.FirstPlaneSelectionId, Definition.SecondPlaneSelectionId)
    ):
        raise ValueError("finite axis must retain its two ordered support selections")
    FirstId, SecondId = HingeValue.selection_ids
    CheckPatPick(PickValues[FirstId], "support_plane", TopId)
    CheckPatPick(PickValues[SecondId], "support_plane", RightId)
    DepthValue = BoundsValue[1][2]
    Center = DepthValue * 0.5
    Border = Center + DepthValue * 0.05
    StartPoint = (0.0, 0.0, (Center - (-Border)) * 1000.0)
    EndPoint = (0.0, 0.0, (Center - Border) * 1000.0)
    if (
        Distance(GetExtVector(Definition.StartMm), StartPoint) >= 1e-10
        or Distance(GetExtVector(Definition.EndMm), EndPoint) >= 1e-10
    ):
        raise ValueError(
            "finite axis endpoints do not follow the directed first plane trim"
        )
