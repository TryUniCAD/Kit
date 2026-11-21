from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumValues import ValueKind
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordParameter import Parameter, ParameterValue
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import (
    MakePlainDoc,
)


# the process cohort must author actual editable rectangle semantics without native files or reconstruction from a generated archive
def MakeRectDimDoc(NameValue: str, IsVariant: bool) -> CadDocument:
    WidthValue, HeightValue, DepthValue = (
        (37.0, 29.0, 12.5) if IsVariant else (54.0, 18.0, 8.25)
    )
    DocumentValue = MakePlainDoc(NameValue, WidthValue, HeightValue, DepthValue)
    SketchValue = DocumentValue.sketches[0]
    OffsetX, OffsetY = (4.125, -7.75) if IsVariant else (0.0, 0.0)
    LineValues = tuple(
        CastValue(LineGeometry, EntityValue.geometry)
        for EntityValue in SketchValue.entities
    )
    EntitiesValue = tuple(
        ReplaceValue(
            EntityValue,
            geometry=LineGeometry(
                PlaneVector(
                    LineValue.start.x + OffsetX,
                    LineValue.start.y + OffsetY,
                ),
                PlaneVector(
                    LineValue.end.x + OffsetX,
                    LineValue.end.y + OffsetY,
                ),
            ),
        )
        for EntityValue, LineValue in zip(SketchValue.entities, LineValues, strict=True)
    )
    Parameters = tuple(
        Parameter(
            f"parameter/{NameText}",
            f"D{IndexValue + 1}",
            ParameterValue(LengthValue, ValueKind.KLength, "mm"),
            owner_id=SketchValue.id,
        )
        for IndexValue, (NameText, LengthValue) in enumerate(
            (("width", WidthValue), ("height", HeightValue))
        )
    )
    AxisRules = tuple(
        SketchRelation(
            f"relation/axis/{IndexValue}",
            "horizontal" if IndexValue % 2 == 0 else "vertical",
            (ConstraintRef(EntityValue.id),),
        )
        for IndexValue, EntityValue in enumerate(EntitiesValue)
    )
    ValueRules = tuple(
        SketchRelation(
            f"relation/length/{IndexValue}",
            "distance",
            (
                ConstraintRef(EntitiesValue[IndexValue].id, "start"),
                ConstraintRef(EntitiesValue[IndexValue].id, "end"),
            ),
            Parameter.id,
        )
        for IndexValue, Parameter in enumerate(Parameters)
    )
    SketchValue = ReplaceValue(
        SketchValue,
        entities=EntitiesValue,
        constraints=(*AxisRules, *ValueRules),
        parameter_ids=tuple(Parameter.id for Parameter in Parameters),
    )
    return ReplaceValue(
        DocumentValue,
        sketches=(SketchValue,),
        parameters=(Parameters[1], DocumentValue.parameters[0], Parameters[0]),
    )
