from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the native configuration index uses its own string and integer row grammar
KStringIntFields = (
    NativeField(
        "Array",
        "items",
        "Framework",
        BodyValue=(
            NativeField("Text", "k"),
            NativeField("Scalar", "v", "i32"),
        ),
        CountValue="n",
    ),
)
