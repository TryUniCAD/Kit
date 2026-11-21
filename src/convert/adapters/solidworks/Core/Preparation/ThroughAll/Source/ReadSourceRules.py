from interchange.geometry.Models.Sketch import Sketch, SketchRelation


# source unary relations must be retained by actual line identity rather than assigned by source array position
def ReadSourceRules(SketchValue: Sketch) -> dict[str, SketchRelation]:
    Result: dict[str, SketchRelation] = {}
    for Relation in SketchValue.constraints:
        if (
            len(Relation.references) != 1
            or Relation.references[0].point
            or not Relation.driving
            or Relation.suppressed
            or Relation.parameter_id is not None
            or Relation.kind not in ("horizontal", "vertical")
        ):
            raise ValueError("source stock has unrepresented constraint intent")
        EntityId = Relation.references[0].entity_id
        if EntityId in Result:
            raise ValueError("source stock has duplicate line relation ownership")
        Result[EntityId] = Relation
    if set(Result) != {Value.id for Value in SketchValue.entities}:
        raise ValueError("source stock relations do not cover every actual line")
    return Result
