from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField


# existing shared stock and dimension fields may use the measured populated branch only inside the local pattern profile
def PatOnlyField(RuleValue: NativeField, OldReason: str) -> NativeField:
    return NativeField(
        "Branch",
        "part_local_pattern",
        BodyValue=(RuleValue,),
        OtherValue=(NativeField("Fail", OldReason),),
        ModeValue="Context",
    )
