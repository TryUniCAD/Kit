from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField


# only the explicit ordinary chamfer context can activate linked output and annotation member fields
def ChmfFieldRule(RuleValue: NativeField, ReasonValue: str) -> NativeField:
    return NativeField(
        "Branch",
        "",
        BodyValue=(RuleValue,),
        OtherValue=(NativeField("Fail", ReasonValue),),
        ModeValue="Expression",
        ExpressionValue=(
            "compare",
            ("Eq",),
            ("lookup", ("context",), ("literal", "cmgr_f658")),
            ("literal", 1),
        ),
    )
