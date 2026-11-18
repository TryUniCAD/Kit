from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordParameter import ParameterValue
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData
from tests.Convert.Solidworks.Research.Construction.RectDimensions.RectDimRequest import (
    RectDimRequest,
)


# equal driving values must remain distinct through actual point ownership rather than dimension value matching
def MakeSquareCase() -> dict[str, object]:
    RequestValue = RectDimRequest("typed equal rectangle lengths", False)
    DocumentValue = CastValue(CadDocument, FromData(RequestValue["document"]))
    (SketchValue,) = DocumentValue.sketches
    EntitiesValue = tuple(
        ReplaceValue(
            EntityValue,
            geometry=LineGeometry(
                PlaneVector(
                    CastValue(LineGeometry, EntityValue.geometry).start.x
                    * 24.675
                    / 54.0,
                    CastValue(LineGeometry, EntityValue.geometry).start.y
                    * 24.675
                    / 18.0,
                ),
                PlaneVector(
                    CastValue(LineGeometry, EntityValue.geometry).end.x * 24.675 / 54.0,
                    CastValue(LineGeometry, EntityValue.geometry).end.y * 24.675 / 18.0,
                ),
            ),
        )
        for EntityValue in SketchValue.entities
    )
    Parameters = tuple(
        (
            ReplaceValue(
                Parameter,
                value=ParameterValue(
                    24.675, Parameter.value.kind, Parameter.value.unit
                ),
            )
            if Parameter.owner_id == SketchValue.id
            else Parameter
        )
        for Parameter in DocumentValue.parameters
    )
    RequestValue["document"] = CastValue(
        object,
        ToData(
            ReplaceValue(
                DocumentValue,
                sketches=(ReplaceValue(SketchValue, entities=EntitiesValue),),
                parameters=Parameters,
            )
        ),
    )
    return RequestValue
