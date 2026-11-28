from dataclasses import replace as ReplaceValue

from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Sketch import ConstraintRef, Sketch


# the reconstructed rectangle must have all four implied ordered endpoint incidences
def ReadPatSk(SketchValue: Sketch) -> Sketch:
    Edges = SketchValue.entities
    Incidences = tuple(
        (ConstraintRef(First.id, "end"), ConstraintRef(Second.id, "start"))
        for First, Second in zip(Edges, (*Edges[1:], *Edges[:1]), strict=True)
    )
    Coincidences = tuple(
        Value for Value in SketchValue.constraints if Value.kind == "coincident"
    )
    if (
        len(Edges) != 4
        or len(Coincidences) != 4
        or {Value.references for Value in Coincidences} != set(Incidences)
        or any(Value.parameter_id is not None for Value in Coincidences)
    ):
        raise ValueError("SOLIDWORKS cold pattern lacks its implied endpoint incidence")
    return ReplaceValue(
        SketchValue,
        entities=tuple(
            ReplaceValue(Value, provenance=None, attributes=FreezeMapping())
            for Value in Edges
        ),
        constraints=tuple(
            ReplaceValue(Value, provenance=None, attributes=FreezeMapping())
            for Value in SketchValue.constraints
            if Value.kind != "coincident"
        ),
        provenance=None,
        attributes=FreezeMapping(),
    )
