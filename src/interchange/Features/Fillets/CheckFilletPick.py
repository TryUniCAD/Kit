from typing import Mapping as TypeMap

from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.Fillets.RadiusFillet import RadiusFillet
from interchange.geometry.Models.Selection import Selection


# a bounded rim query must name the actual preceding edge rather than merely contain selection text
def CheckFilletPick(
    StepValue: FeatureStep,
    Definition: RadiusFillet,
    Selections: TypeMap[str, Selection],
) -> tuple[str, str]:
    Selected = Selections.get(Definition.EdgeSelectionId)
    if (
        StepValue.selection_ids != (Definition.EdgeSelectionId,)
        or Selected is None
        or len(Selected.path) != 2
    ):
        raise ValueError(
            "radius fillet requires exactly one resolved upper rim selection"
        )
    BodyPath, FeaturePath = Selected.path
    if (
        BodyPath.entity_kind != "body"
        or not BodyPath.entity_id.strip()
        or BodyPath.subelement
        or FeaturePath.entity_kind != "feature"
        or not FeaturePath.entity_id.strip()
        or FeaturePath.subelement != "upper_rim"
    ):
        raise ValueError("radius fillet requires a body and predecessor upper rim path")
    if (
        StepValue.input_feature_ids != (FeaturePath.entity_id,)
        or FeaturePath.entity_id == StepValue.id
    ):
        raise ValueError(
            "radius fillet requires exactly one prior selected feature dependency"
        )
    if Selected.query != {
        "entity_kind": "edge",
        "curve_kind": "circle",
        "position": "upper_rim",
        "source_feature_id": FeaturePath.entity_id,
    }:
        raise ValueError(
            "radius fillet requires the selected predecessor circular upper rim query"
        )
    return BodyPath.entity_id, FeaturePath.entity_id
