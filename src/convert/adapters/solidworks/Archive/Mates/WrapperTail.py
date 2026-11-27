from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# component plane and cylinder owners share the native wrapper state after their first owned reference
KWrapperTail = (
    NativeField("Scalar", "f68", "u16"),
    NativeField("Node", "f60", "moComponent_c"),
    NativeField("Scalar", "f6c", "i32"),
    NativeField("Scalar", "f08", "i32"),
    NativeField(
        "Present",
        "has_f10",
        "u16",
        BodyValue=(NativeField("Embed", "f10", "mgXform_c.restore"),),
    ),
    NativeField(
        "Present",
        "has_f18",
        "u16",
        BodyValue=(NativeField("Embed", "f18", "mgXform_c.restore"),),
    ),
    NativeField("Scalar", "f0c", "i32"),
    NativeField("Scalar", "f20", "i32"),
    NativeField("Scalar", "f74", "i32"),
    NativeField("Scalar", "f78", "i32"),
    NativeField("Scalar", "f7c", "i32"),
    NativeField("Scalar", "f50", "i32"),
    NativeField("Scalar", "f70", "i32"),
    NativeField(
        "Branch",
        "ctx874",
        BodyValue=(
            NativeField(
                "Present",
                "has_f80",
                "i32",
                BodyValue=(NativeField("Embed", "f80", "moReferencedConfiguration_c"),),
            ),
        ),
        ModeValue="Context",
    ),
    NativeField("Scalar", "f34", "i32"),
    NativeField("Scalar", "f30", "i32"),
    NativeField("Scalar", "f98", "i32"),
    NativeField("Scalar", "f38", "i32"),
)
