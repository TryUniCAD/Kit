from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# linked atom nodes preserve both counted index arrays and every typed row alias
KLinkedAtomFields = (
    NativeField("Scalar", "f08", "i32"),
    NativeField("Embed", "f90", "su_CDWordArray"),
    NativeField("Embed", "fd0", "su_CDWordArray"),
    NativeField(
        "Array",
        "ff0",
        "u32",
        BodyValue=(
            NativeField("Scalar", "key", "i32"),
            NativeField("Node", "o"),
        ),
        CountValue="nf0",
    ),
    NativeField(
        "Array",
        "f100",
        "u32",
        BodyValue=(
            NativeField("Scalar", "key", "i32"),
            NativeField("Node", "o"),
        ),
        CountValue="n100",
    ),
    NativeField(
        "Array",
        "f110",
        "u32",
        BodyValue=(
            NativeField("Scalar", "key", "i32"),
            NativeField("Node", "o"),
        ),
        CountValue="n110",
    ),
    NativeField(
        "Array",
        "f120",
        "u32",
        BodyValue=(
            NativeField("Scalar", "key", "i32"),
            NativeField("Node", "o"),
        ),
        CountValue="n120",
    ),
)
