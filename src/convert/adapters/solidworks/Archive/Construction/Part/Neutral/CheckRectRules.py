from interchange.Records.RecordParameter import Parameter
from interchange.geometry.Models.Sketch import ConstraintRef, Sketch


# the admitted rectangle must carry the six actual editable relations rather than silently inventing solver intent from its current shape
def CheckRectRules(
    SketchValue: Sketch, Parameters: tuple[Parameter, Parameter]
) -> None:
    if (
        len(SketchValue.constraints) != 6
        or len(SketchValue.closed_profile_entity_ids) != 1
    ):
        raise ValueError(
            "dimensioned rectangle requires four axis relations and two point distance drivers"
        )
    OrderValue = SketchValue.closed_profile_entity_ids[0]
    if len(OrderValue) != 4:
        raise ValueError("dimensioned rectangle requires four ordered line roles")
    ExpectedValues = tuple(
        (
            "horizontal" if IndexValue % 2 == 0 else "vertical",
            (ConstraintRef(EntityId),),
            None,
        )
        for IndexValue, EntityId in enumerate(OrderValue)
    ) + tuple(
        (
            "distance",
            (
                ConstraintRef(OrderValue[IndexValue], "start"),
                ConstraintRef(OrderValue[IndexValue], "end"),
            ),
            Parameter.id,
        )
        for IndexValue, Parameter in enumerate(Parameters)
    )
    for RelationValue in SketchValue.constraints:
        if (
            not RelationValue.driving
            or RelationValue.suppressed
            or RelationValue.attributes
        ):
            raise ValueError(
                "rectangle relations must remain active driving unextended design intent"
            )
    ActualValues = tuple(
        (RelationValue.kind, RelationValue.references, RelationValue.parameter_id)
        for RelationValue in SketchValue.constraints
    )
    if any(ActualValues.count(ExpectedValue) != 1 for ExpectedValue in ExpectedValues):
        raise ValueError(
            "rectangle axis and distance relations must bind their exact owned line and endpoint roles"
        )
