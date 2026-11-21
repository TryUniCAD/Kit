from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# embedded light properties retain the empty physical owner while populated values need further evidence
KLightPropFields = (
    NativeField("Length", "n", "i32", CountValue="props"),
    NativeField(
        "Branch",
        "n",
        BodyValue=(NativeField("Fail", "populated light user properties"),),
        ModeValue="Nonzero",
    ),
)
