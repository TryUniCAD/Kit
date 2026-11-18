from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import SketchEntity
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData
from tests.Convert.Solidworks.Research.Construction.Part.BlindCaseInput import (
    BlindCaseInput,
)


# the polygon process needs a genuine neutral document with independently ordered sketch lines and no native payload
def MakePolygonCase(
    NameValue: str,
    VerticesValue: tuple[tuple[float, float], ...],
    IsVariant: bool,
) -> dict[str, object]:
    Request = BlindCaseInput(NameValue, IsVariant)
    DocumentValue = CastValue(CadDocument, FromData(Request["document"]))
    IdsValue = tuple(f"edge/{IndexValue}" for IndexValue in range(len(VerticesValue)))
    NextPoints = VerticesValue[1:] + VerticesValue[:1]
    EntitiesValue = tuple(
        SketchEntity(
            EntityId,
            GeometryKind.KLine,
            LineGeometry(PlaneVector(*StartValue), PlaneVector(*EndValue)),
        )
        for EntityId, StartValue, EndValue in zip(
            IdsValue, VerticesValue, NextPoints, strict=True
        )
    )
    SketchValue = ReplaceValue(
        DocumentValue.sketches[0],
        entities=EntitiesValue,
        closed_profile_entity_ids=(IdsValue,),
    )
    Request["document"] = ToData(ReplaceValue(DocumentValue, sketches=(SketchValue,)))
    return Request
