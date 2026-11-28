from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField


# saved open shells share stock fields behind an explicit layout guard
def ShellFieldRule(ReasonValue: str, *RulesValue: NativeField) -> NativeField:
    return NativeField(
        "Branch",
        "",
        BodyValue=RulesValue,
        OtherValue=(NativeField("Fail", ReasonValue),),
        ModeValue="Expression",
        ExpressionValue=(
            "lookup_or",
            ("context",),
            ("literal", "read_shell"),
            ("literal", 0),
        ),
    )
