from interchange.geometry.Models.Sketch import ConstraintRef, Sketch


# two point distances must select the actual oriented width and height edges with their own parameters
def CheckDriverRefs(SketchValue: Sketch) -> None:
    (LoopValue,) = SketchValue.closed_profile_entity_ids
    Drivers = tuple(
        RowValue for RowValue in SketchValue.constraints if RowValue.kind == "distance"
    )
    assert tuple(
        (RowValue.parameter_id, RowValue.references) for RowValue in Drivers
    ) == tuple(
        (ParameterId, (ConstraintRef(EdgeId, "start"), ConstraintRef(EdgeId, "end")))
        for ParameterId, EdgeId in zip(
            SketchValue.parameter_ids, LoopValue[:2], strict=True
        )
    )
