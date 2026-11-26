from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# each reference id has its own native count and a separate series of guid values
KBlockRefRows = (
    NativeField("Scalar", "key", "i32"),
    NativeField("Length", "m", "i32", CountValue="guids", ModeValue="Positive"),
    NativeField(
        "Repeat",
        "guids",
        BodyValue=(NativeField("Bytes", "g", MaskValue=16),),
        CountValue="m",
        ModeValue="Positive",
    ),
)

# the empty sketch map still carries its owner and its two distinct native length words
KBlockMapFields = (
    NativeField("Scalar", "f18", "i32"),
    NativeField("Node", "f30"),
    NativeField("Length", "n70", "i32", CountValue="f68", ModeValue="Positive"),
    NativeField(
        "Repeat",
        "f68",
        BodyValue=KBlockRefRows,
        CountValue="n70",
        ModeValue="Positive",
    ),
    NativeField("Length", "n98", "u32", CountValue="f90", ModeValue="SignedPositive"),
    NativeField(
        "Repeat",
        "f90",
        BodyValue=(
            NativeField("Bytes", "k", MaskValue=16),
            NativeField("Bytes", "v", MaskValue=16),
            NativeField("Scalar", "i", "i32"),
            NativeField("Text", "name"),
        ),
        CountValue="n98",
        ModeValue="SignedPositive",
    ),
)
