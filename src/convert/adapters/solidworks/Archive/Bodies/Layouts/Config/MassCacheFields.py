from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# each cache entry reads its atom rows before the conditional mass property body
KMassCacheFields = (
    NativeField("Length", "n10", "i32", CountValue="f08"),
    NativeField(
        "Repeat",
        "f08",
        BodyValue=(
            NativeField("Scalar", "atom", "i32"),
            NativeField("Scalar", "v", "i32"),
            NativeField("Scalar", "d", "f64"),
        ),
        CountValue="n10",
    ),
    NativeField(
        "Branch",
        "n10",
        BodyValue=(NativeField("Embed", "f18", "moMassProp_c"),),
        ModeValue="Nonzero",
    ),
)
