from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# each reference id has its own native count and a separate series of guid values
KBlockRefRows = (
    NativeField("Scalar", "key", "i32"),
    NativeField("Length", "m", "i32", CountValue="guids"),
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
    NativeField("Length", "n70", "i32", CountValue="f68"),
    NativeField(
        "Repeat",
        "f68",
        BodyValue=KBlockRefRows,
        CountValue="n70",
        ModeValue="Positive",
    ),
    NativeField("Length", "n98", "u32", CountValue="f90"),
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

# the two concrete owner suffixes reuse the same feature body and keep embedded records distinct
KOwnerFields = MappingProxyType(
    {
        "moSketchBlockMgr_c": (
            NativeField("Base", "moFeature_c"),
            NativeField("Bytes", "f380", MaskValue=16),
            NativeField(
                "Embed", "blocks", "moRefIdToSketchBlockListMap_c.FUN_4c9080f0"
            ),
        ),
        "moRefIdToSketchBlockListMap_c.FUN_4c9080f0": KBlockMapFields,
        "moPrtExplViewManager_c": (
            NativeField("Base", "moFeature_c"),
            NativeField("Node", "f358"),
            NativeField("Node", "f360"),
            NativeField("Scalar", "f398", "f64"),
            NativeField("Scalar", "f3a0", "i32"),
            NativeField("Scalar", "f3a4", "i32"),
            NativeField("Embed", "f368", "su_CMapWordToOb.Serialize"),
        ),
        "su_CMapWordToOb.Serialize": (
            NativeField(
                "Array",
                "items",
                "Count",
                BodyValue=(NativeField("Scalar", "k", "u16"), NativeField("Node", "v")),
                CountValue="n",
            ),
        ),
    }
)
