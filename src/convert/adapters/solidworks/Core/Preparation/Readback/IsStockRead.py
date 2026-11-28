from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Adapter import KSourceFormatKey
from convert.adapters.solidworks.Core.Preparation.IsStockChain import IsStockOps
from convert.adapters.solidworks.Core.Preparation.Readback.StockReadSteps import (
    StockReadSteps,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureExtrude import ExtrudeFeature


# selection reaches the stock planner only for the typed native readback shape
def IsStockRead(DocumentValue: CadDocument) -> bool:
    if (
        DocumentValue.source.format_id != KPartFormatId
        or DocumentValue.source.container_version != "4"
        or DocumentValue.metadata.get(KSourceFormatKey) != KPartFormatId
        or len(DocumentValue.sketches) != 3
        or len(DocumentValue.bodies) != 2
        or len(DocumentValue.selections) != 1
    ):
        return False
    StepsValue = StockReadSteps(DocumentValue)
    return (
        IsStockOps(StepsValue)
        and all(
            type(StepValue.definition) is ExtrudeFeature for StepValue in StepsValue
        )
        and sum(
            SketchValue.attributes.get("typed_line_loop") is True
            for SketchValue in DocumentValue.sketches
        )
        == 2
    )
