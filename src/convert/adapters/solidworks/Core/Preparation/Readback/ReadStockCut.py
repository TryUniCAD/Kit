from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdDisc import (
    ReadDiscEntity,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Sketch import Sketch


# the through cut keeps its historical stock dependency and typed free circle
def ReadStockCut(
    DocumentValue: CadDocument,
    CutValue: FeatureStep,
    StockValue: FeatureStep,
    SketchValue: Sketch,
) -> tuple[FeatureStep, Sketch]:
    Profiles = tuple(
        StepValue.id
        for StepValue in DocumentValue.feature_timeline
        if StepValue.id != CutValue.id and StepValue.sketch_id == SketchValue.id
    )
    if len(Profiles) != 1 or CutValue.input_feature_ids != (StockValue.id, *Profiles):
        raise ValueError("SOLIDWORKS cold cut lacks its selected stock and profile")
    (Entity,) = SketchValue.entities
    Geometry = Entity.geometry
    if type(Geometry) is not CircleGeometry:
        raise ValueError("SOLIDWORKS cold cut requires its actual free circle")
    return (
        ReplaceValue(
            CutValue,
            order=2,
            input_feature_ids=(StockValue.id,),
            attributes=FreezeMapping(),
            provenance=None,
        ),
        ReplaceValue(
            SketchValue,
            entities=(ReadDiscEntity(Entity, Geometry.radius),),
            attributes=FreezeMapping(),
            provenance=None,
        ),
    )
