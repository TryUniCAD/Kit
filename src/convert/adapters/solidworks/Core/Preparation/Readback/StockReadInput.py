from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Readback.ReadStockBoss import (
    ReadStockBoss,
)
from convert.adapters.solidworks.Core.Preparation.Readback.ReadStockCut import (
    ReadStockCut,
)
from convert.adapters.solidworks.Core.Preparation.Readback.StockReadSteps import (
    StockReadSteps,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordTopology import TopologyCounts


# clean construction inputs leave all retained source state for full regeneration comparison
def StockReadInput(DocumentValue: CadDocument, NameValue: str) -> CadDocument:
    FrontValue, RightValue, CutValue = StockReadSteps(DocumentValue)
    Sketches = {SketchValue.id: SketchValue for SketchValue in DocumentValue.sketches}
    FrontDraw, RightDraw, CutDraw = (
        Sketches[StepValue.sketch_id or ""]
        for StepValue in (FrontValue, RightValue, CutValue)
    )
    Front, FrontDepth, FrontLoop, FrontPlane = ReadStockBoss(
        DocumentValue, FrontValue, FrontDraw, 0
    )
    Right, RightDepth, RightLoop, RightPlane = ReadStockBoss(
        DocumentValue, RightValue, RightDraw, 1
    )
    CutStep, DiscValue = ReadStockCut(DocumentValue, CutValue, FrontValue, CutDraw)
    (Config,) = DocumentValue.configurations
    (Choice,) = DocumentValue.selections
    return ReplaceValue(
        DocumentValue,
        source=ReplaceValue(DocumentValue.source, attributes=FreezeMapping()),
        configurations=(ReplaceValue(Config, attributes=FreezeMapping()),),
        parameters=(FrontDepth, RightDepth),
        support_planes=(FrontPlane, RightPlane),
        sketches=(FrontLoop, RightLoop, DiscValue),
        selections=(ReplaceValue(Choice, provenance=None),),
        feature_timeline=(Front, Right, CutStep),
        bodies=tuple(
            ReplaceValue(
                BodyValue,
                topology=TopologyCounts(),
                attributes=FreezeMapping(),
                provenance=None,
            )
            for BodyValue in DocumentValue.bodies
        ),
        brep=None,
        diagnostics=(),
        metadata=FreezeMapping({"name": NameValue}),
        capabilities=frozenset(),
    )
