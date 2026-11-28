from interchange.geometry.Models.Sketch import ConstraintRef, Sketch


# radial control and centre fixing must reference their actual independent circle roles
def IsCircDiameter(SketchValue: Sketch, EntityId: str, RadialId: str) -> bool:
    if len(SketchValue.constraints) != 2:
        raise ValueError(
            "circle profile requires an actual centre fix and radial driver"
        )
    for RuleValue in SketchValue.constraints:
        if not RuleValue.driving or RuleValue.suppressed or RuleValue.attributes:
            raise ValueError(
                "circle relations must remain active driving and unextended"
            )
    FixedValue = tuple(
        RuleValue
        for RuleValue in SketchValue.constraints
        if RuleValue.kind == "fixed"
        and RuleValue.references == (ConstraintRef(EntityId, "center"),)
        and RuleValue.parameter_id is None
    )
    RadialValue = tuple(
        RuleValue
        for RuleValue in SketchValue.constraints
        if RuleValue.kind in ("radius", "diameter")
        and RuleValue.references == (ConstraintRef(EntityId),)
        and RuleValue.parameter_id == RadialId
    )
    if len(FixedValue) != 1 or len(RadialValue) != 1:
        raise ValueError(
            "circle relations must bind the centre and actual radial parameter"
        )
    return RadialValue[0].kind == "diameter"
