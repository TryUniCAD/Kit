from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# point and dimension wrappers share the actual owner and optional reference transforms
KRefWrapperTransforms = (
    NativeField("Scalar", "f68", "u16"),
    NativeField("Node", "f60", "moComponent_c"),
    NativeField("Scalar", "f6c", "i32"),
    NativeField("Scalar", "f08", "i32"),
    NativeField("Scalar", "has_f10", "u16"),
    NativeField(
        "Branch",
        "has_f10",
        BodyValue=(NativeField("Embed", "f10", "mgXform_c.restore"),),
        ModeValue="Nonzero",
    ),
    NativeField("Scalar", "has_f18", "u16"),
    NativeField(
        "Branch",
        "has_f18",
        BodyValue=(NativeField("Embed", "f18", "mgXform_c.restore"),),
        ModeValue="Nonzero",
    ),
)

# the native wrapper stores its reference words immediately after the transform fields
KRefWrapperTailFields = (
    *KRefWrapperTransforms,
    NativeField("Scalar", "f0c", "i32"),
    NativeField("Scalar", "f20", "i32"),
    NativeField("Scalar", "f74", "i32"),
    NativeField("Scalar", "f78", "i32"),
    NativeField("Scalar", "f7c", "i32"),
    NativeField("Scalar", "f50", "i32"),
    NativeField("Scalar", "f70", "i32"),
    NativeField("Scalar", "f34", "i32"),
    NativeField("Scalar", "f30", "i32"),
    NativeField("Scalar", "f98", "i32"),
    NativeField("Scalar", "f38", "i32"),
)
