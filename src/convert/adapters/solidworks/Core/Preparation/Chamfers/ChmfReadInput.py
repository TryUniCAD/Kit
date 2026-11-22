from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Chamfers.PlanChmfPart import (
    ReadChmfParams,
)
from convert.adapters.solidworks.Core.Preparation.Readback.ColdReadInput import (
    ColdReadInput,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureKinds import ChamferFeature


# measured source intent uses the real stock and modifier drivers while full regeneration independently verifies every observed field
def ChmfReadInput(Document: CadDocument, NameValue: str) -> CadDocument:
    if len(Document.bodies) != 1:
        raise ValueError("SOLIDWORKS chamfer readback requires its sole result body")
    (BodyValue,) = Document.bodies
    Steps = {Value.id: Value for Value in Document.feature_timeline}
    Modifier = Steps.get(BodyValue.final_feature_id or "")
    if (
        Modifier is None
        or type(Modifier.definition) is not ChamferFeature
        or len(Modifier.input_feature_ids) != 1
    ):
        raise ValueError(
            "SOLIDWORKS chamfer readback requires its actual preceding boss"
        )
    (StockId,) = Modifier.input_feature_ids
    Stock = Steps.get(StockId)
    if Stock is None:
        raise ValueError("SOLIDWORKS chamfer readback lacks its actual stock")
    DepthValue, Drivers = ReadChmfParams(Document, Stock, Modifier)
    StockInput = ColdReadInput(
        ReplaceValue(
            Document,
            parameters=(DepthValue,),
            feature_timeline=tuple(
                Value for Value in Document.feature_timeline if Value is not Modifier
            ),
            bodies=(ReplaceValue(BodyValue, final_feature_id=StockId),),
        ),
        NameValue,
    )
    return ReplaceValue(
        StockInput,
        parameters=(
            *StockInput.parameters,
            *(
                ReplaceValue(Value, attributes=FreezeMapping(), provenance=None)
                for Value in Drivers
            ),
        ),
        selections=tuple(
            ReplaceValue(Value, provenance=None) for Value in Document.selections
        ),
        feature_timeline=(
            *StockInput.feature_timeline,
            ReplaceValue(
                Modifier, order=1, attributes=FreezeMapping(), provenance=None
            ),
        ),
        bodies=(ReplaceValue(StockInput.bodies[0], final_feature_id=Modifier.id),),
    )
