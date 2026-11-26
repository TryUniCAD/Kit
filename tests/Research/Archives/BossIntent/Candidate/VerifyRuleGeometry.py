from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation


# the left and bottom dimension operands must retain their roles and lengths after request preparation
def VerifyRuleGeom(
    Source: CadDocument, Target: CadDocument, SavedRows: tuple[SketchRelation, ...]
) -> None:
    (SketchValue,), (TargetSketch,) = Source.sketches, Target.sketches
    ((Bottom, Right, Upper, LeftEdge),) = SketchValue.closed_profile_entity_ids
    EntityById = {Entity.id: Entity for Entity in SketchValue.entities}
    TargetEntities = {Entity.id: Entity for Entity in TargetSketch.entities}
    TargetRules = {Relation.id: Relation for Relation in TargetSketch.constraints}
    assert [RuleValue.kind for RuleValue in SavedRows] == [
        "horizontal",
        "vertical",
        "horizontal",
        "vertical",
        "distance",
        "distance",
        "coincident",
    ]
    for RuleValue, EdgeId in zip(
        SavedRows[:4], (Bottom, Right, Upper, LeftEdge), strict=True
    ):
        assert (
            RuleValue.references == (ConstraintRef(EdgeId),)
            and RuleValue.parameter_id is None
        )
        assert TargetEntities[EdgeId].geometry == EntityById[EdgeId].geometry
    for RuleValue in SavedRows:
        TargetRule = TargetRules[RuleValue.id]
        assert (TargetRule.kind, TargetRule.references, TargetRule.parameter_id) == (
            RuleValue.kind,
            RuleValue.references,
            RuleValue.parameter_id,
        )
    (Owner,) = [
        StepValue
        for StepValue in Source.feature_timeline
        if StepValue.sketch_id == SketchValue.id and StepValue.operation is None
    ]
    Params = {ParamValue.id: ParamValue for ParamValue in Source.parameters}
    TargetParams = {ParamValue.id: ParamValue for ParamValue in Target.parameters}
    for RuleValue, EdgeId, ParamName, Millimetres, AxisEnd, Slots in (
        (SavedRows[4], LeftEdge, "height_mm", 20.0, (0.0, 20.0), ("end", "start")),
        (SavedRows[5], Bottom, "width_mm", 40.0, (40.0, 0.0), ("start", "end")),
    ):
        assert RuleValue.references == tuple(
            ConstraintRef(EdgeId, SlotValue) for SlotValue in Slots
        )
        assert RuleValue.parameter_id is not None
        Parameter = Params[RuleValue.parameter_id]
        TargetParam = TargetParams[RuleValue.parameter_id]
        assert Parameter.name == ParamName and Parameter.owner_id == Owner.id
        assert (
            Parameter.value.value == RuleValue.attributes["native_value"] == Millimetres
        )
        assert Parameter.value.unit == "mm" and TargetParam.value == Parameter.value
        assert TargetParam.owner_id == Parameter.owner_id
        Geometry = EntityById[EdgeId].geometry
        assert (
            isinstance(Geometry, LineGeometry)
            and TargetEntities[EdgeId].geometry == Geometry
        )
        First, Second = (
            (Geometry.end, Geometry.start)
            if Slots[0] == "end"
            else (Geometry.start, Geometry.end)
        )
        assert (First.x, First.y) == (0.0, 0.0) and (Second.x, Second.y) == AxisEnd
