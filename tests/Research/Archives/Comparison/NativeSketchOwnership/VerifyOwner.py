from interchange.document.Models.DocumentModel import CadDocument


# projecting a reported owner must preserve native constraint and operand ordering through the real comparison
def VerifyOwner(Document: CadDocument, Observation: dict[str, object]) -> None:
    (SketchValue,) = Document.sketches
    Owner = Document.feature_timeline[24]
    assert Owner.id == "sldprt:feature:26" and Owner.sketch_id == SketchValue.id
    assert SketchValue.id == "sldprt:sketch:26"
    assert Observation["path"] == "/feature_timeline/24/sketch_id"
    assert Observation["owner_id"] == Owner.id
    assert Observation["sketch_id"] == SketchValue.id
    assert Observation["source_span"] == {
        "stream": "Contents/Config-0-ResolvedFeatures",
        "offset": 5578,
        "length": 6437,
    }
    assert len(SketchValue.constraints) == 11
    assert Observation["constraints"] == [
        {
            "constraint_id": Constraint.id,
            "kind": Constraint.kind,
            "parameter_id": Constraint.parameter_id,
            "references": [
                {"entity_id": Operand.entity_id, "point": Operand.point}
                for Operand in Constraint.references
            ],
        }
        for Constraint in SketchValue.constraints
    ]
    assert tuple(
        Constraint.parameter_id
        for Constraint in SketchValue.constraints
        if Constraint.parameter_id is not None
    ) == ("sldprt:parameter:26:height_mm", "sldprt:parameter:26:width_mm")
