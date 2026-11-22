from dataclasses import replace as ReplaceValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation
from interchange.Records.RecordParameter import Parameter, ParameterValue
from tests.Convert.Solidworks.NestedWriting.MakeNestDoc import MakeNestDoc


# the existing neutral leaf can add live horizontal vertical and point distance intent without native inputs
def MakeDimNest(Translated: bool = False) -> CadDocument:
    DocumentValue = (
        MakeNestDoc(((2.5, 0.0), (15.0, 0.0), (15.0, 9.0), (2.5, 9.0)))
        if Translated
        else MakeNestDoc()
    )
    WidthValue = 12.5 if Translated else 17.0
    GraphValue = DocumentValue.assembly
    assert GraphValue is not None
    (Member,) = GraphValue.documents
    PartValue = Member.document
    (SketchValue,) = PartValue.sketches
    (OrderValue,) = SketchValue.closed_profile_entity_ids
    Drivers = tuple(
        Parameter(
            Identity,
            NameValue,
            ParameterValue(LengthValue, ValueKind.KLength, "mm"),
            ParameterRole.KDriving,
            owner_id=SketchValue.id,
        )
        for Identity, NameValue, LengthValue in (
            ("parameter/outline-width", "D1", WidthValue),
            ("parameter/outline-height", "D2", 9.0),
        )
    )
    Relations = tuple(
        SketchRelation(
            f"constraint/axis/{Index}",
            "horizontal" if Index % 2 == 0 else "vertical",
            (ConstraintRef(EdgeId),),
        )
        for Index, EdgeId in enumerate(OrderValue)
    ) + tuple(
        SketchRelation(
            f"constraint/length/{Index}",
            "distance",
            (
                ConstraintRef(OrderValue[Index], "start"),
                ConstraintRef(OrderValue[Index], "end"),
            ),
            Parameter.id,
        )
        for Index, Parameter in enumerate(Drivers)
    )
    DimSketch = ReplaceValue(
        SketchValue,
        constraints=Relations,
        parameter_ids=tuple(Value.id for Value in Drivers),
    )
    DimPart = ReplaceValue(
        PartValue, sketches=(DimSketch,), parameters=(*Drivers, *PartValue.parameters)
    )
    return ReplaceValue(
        DocumentValue,
        assembly=ReplaceValue(
            GraphValue, documents=(ReplaceValue(Member, document=DimPart),)
        ),
    )
