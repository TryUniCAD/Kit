from dataclasses import replace as ReplaceValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Sketch import ConstraintRef


# edited relation operands must remain structurally valid to test identity rather than malformed json
def ChangeRules(InputDoc: CadDocument) -> tuple[CadDocument, ...]:
    SketchValue = InputDoc.sketches[0]
    Relations = SketchValue.constraints
    Perimeter = SketchValue.closed_profile_entity_ids[0]
    LocalCorner = next(
        Entity.id
        for Entity in SketchValue.entities
        if Entity.construction
        and not Entity.fixed
        and Entity.geometry == SketchValue.entities[-1].geometry
    )
    Changes = (
        (4, (ConstraintRef(Perimeter[1], "start"), ConstraintRef(Perimeter[1], "end"))),
        (4, Relations[4].references[::-1]),
        (10, (ConstraintRef(LocalCorner), Relations[10].references[1])),
    )
    return tuple(
        ReplaceValue(
            InputDoc,
            sketches=(
                ReplaceValue(
                    SketchValue,
                    constraints=Relations[:Position]
                    + (ReplaceValue(Relations[Position], references=Operands),)
                    + Relations[Position + 1 :],
                ),
            ),
        )
        for Position, Operands in Changes
    )
