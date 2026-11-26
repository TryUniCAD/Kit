from interchange.geometry.Models.Sketch import SketchRelation


# persisted relation evidence must retain every saved operand in reader order
def CheckSavedOrder(Observed: object, SavedRows: tuple[SketchRelation, ...]) -> None:
    ExpectedRows = [
        [
            RuleValue.id,
            RuleValue.kind,
            [[RefValue.entity_id, RefValue.point] for RefValue in RuleValue.references],
            RuleValue.parameter_id,
        ]
        for RuleValue in SavedRows
    ]
    assert Observed == ExpectedRows, "persisted P03 saved relation order differs"
