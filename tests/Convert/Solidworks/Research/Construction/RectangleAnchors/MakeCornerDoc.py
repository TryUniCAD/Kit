from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector
from tests.Convert.Solidworks.Research.Construction.RectDimensions.MakeRectDimDoc import (
    MakeRectDimDoc,
)


# origin based synthetic inputs must preserve actual neutral rectangle driver ownership while independently choosing all three dimensions
def MakeCornerDoc(
    NameValue: str, LengthValue: float, WidthValue: float, DepthValue: float
) -> CadDocument:
    DocumentValue = MakeRectDimDoc(NameValue, False)
    SketchValue, FeatureValue = (
        DocumentValue.sketches[0],
        DocumentValue.feature_timeline[0],
    )
    VerticesValue = (
        (0.0, 0.0),
        (LengthValue, 0.0),
        (LengthValue, WidthValue),
        (0.0, WidthValue),
    )
    EntitiesValue = tuple(
        ReplaceValue(
            EntityValue,
            geometry=LineGeometry(
                PlaneVector(*VerticesValue[IndexValue]),
                PlaneVector(*VerticesValue[(IndexValue + 1) % 4]),
            ),
        )
        for IndexValue, EntityValue in enumerate(SketchValue.entities)
    )
    LengthValues = {
        "parameter/width": LengthValue,
        "parameter/height": WidthValue,
        "parameter/depth": DepthValue,
    }
    Parameters = tuple(
        ReplaceValue(
            Parameter,
            value=ReplaceValue(Parameter.value, value=LengthValues[Parameter.id]),
        )
        for Parameter in DocumentValue.parameters
    )
    DepthParameter = next(
        Parameter for Parameter in Parameters if Parameter.id == "parameter/depth"
    )
    DefinitionValue = ReplaceValue(
        CastValue(ExtrudeFeature, FeatureValue.definition), length=DepthParameter.value
    )
    return ReplaceValue(
        DocumentValue,
        sketches=(ReplaceValue(SketchValue, entities=EntitiesValue),),
        parameters=Parameters,
        feature_timeline=(ReplaceValue(FeatureValue, definition=DefinitionValue),),
    )
