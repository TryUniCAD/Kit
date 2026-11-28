from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the observed material branches have an empty user property record
KVisualPropFields = (
    NativeField("Length", "n", "i32", CountValue="props"),
    NativeField(
        "Branch",
        "n",
        BodyValue=(NativeField("Fail", "populated material user properties"),),
        ModeValue="Nonzero",
    ),
)
