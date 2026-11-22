from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# native visual fields select the physically based appearance record after the material block
KMatVisualFields = (
    NativeField("Scalar", "f0c", "u32"),
    NativeField("Scalar", "f14", "u32"),
    NativeField("Scalar", "f18", "u32"),
    NativeField("Embed", "f20", "uoMaterialProperties.restore"),
    NativeField("Text", "f40"),
    NativeField("Scalar", "f48", "i32"),
    NativeField("Scalar", "f4c", "i32"),
    NativeField("Text", "f50"),
    NativeField("Scalar", "f58", "i32"),
    NativeField("Scalar", "f5c", "i32"),
    NativeField("Scalar", "f78", "i32"),
    NativeField("Scalar", "f7c", "i32"),
    NativeField("Scalar", "f80", "i32"),
    NativeField("Scalar", "has88", "i32"),
    NativeField(
        "Branch",
        "has88",
        BodyValue=(NativeField("Embed", "f88", "uoDSPBRProperties_c.restore"),),
        ModeValue="Nonzero",
    ),
)
