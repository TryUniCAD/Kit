from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequireExtrusion import (
    RequireExtrude,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeatureExtrude import ExtrudeEnd
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection, SelectPathElem
from interchange.geometry.Models.VectorSpace import SpaceVector


# a selected through cut must keep its exact preceding body instead of promoting the scope
def CheckStockPick(
    StockValue: FeatureStep, CutValue: FeatureStep, ChoiceValue: Selection
) -> None:
    if (
        ChoiceValue.path != (SelectPathElem("feature", StockValue.id, "body"),)
        or ChoiceValue.name not in ("Selected stock", f"{StockValue.name} body")
        or ChoiceValue.query
        or ChoiceValue.point is not None
        or ChoiceValue.provenance is not None
        or ChoiceValue.attributes
    ):
        raise ValueError(
            "the cut requires one implicit label and the actual historical Front stock"
        )
    Definition = RequireExtrude(
        CutValue,
        BooleanOp.KCutOperation,
        (StockValue.id,),
        ExpectedSelections=(ChoiceValue.id,),
    )
    if (
        Definition.end_condition != ExtrudeEnd.KThroughAll
        or Definition.length is not None
        or Definition.second_length is not None
        or Definition.second_end_condition is not None
        or Definition.symmetric is not False
        or Definition.reversed is not False
        or Definition.direction != SpaceVector(*PrincipalFrame("z").NormalValue)
        or CutValue.parameter_ids
    ):
        raise ValueError(
            "the cut requires a forward depthless through-all end on the Front stock"
        )
