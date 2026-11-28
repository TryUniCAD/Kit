from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# only the pattern direction line uses a datum selection within the shared wrapper body
KPatternDatumFields = (
    NativeField(
        "Branch",
        "moLineRef_w",
        OtherValue=(NativeField("Fail", "pattern datum requires a line wrapper"),),
        ModeValue="Class",
    ),
    NativeField("Node", "f58", "moCompRefPlane_c"),
)
