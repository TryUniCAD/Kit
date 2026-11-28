from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField


# formerly unresolved rows can be traversed only for the concrete imported feature
def LocalBodyBranch(*FieldsValue: NativeField) -> NativeField:
    Failure = NativeField("Fail", "unqualified local import row")
    return NativeField(
        "Branch",
        "moBaseBody_c",
        ModeValue="Class",
        BodyValue=(
            NativeField(
                "Branch",
                "cmgr_f658",
                ModeValue="Context",
                BodyValue=FieldsValue,
                OtherValue=(Failure,),
            ),
        ),
        OtherValue=(Failure,),
    )
