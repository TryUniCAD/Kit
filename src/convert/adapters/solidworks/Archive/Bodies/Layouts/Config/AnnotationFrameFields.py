from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current native field order supplies both directions without saved document values
KAnnotationFrameFields = MappingProxyType(
    {
        "moGTolDlgDataFrame_c": (
            NativeField("Text", "f08"),
            NativeField("Scalar", "f28", "u8"),
            NativeField("Text", "f30"),
            NativeField("Text", "f38"),
            NativeField("Scalar", "f40", "u8"),
            NativeField("Text", "f48"),
            NativeField("Text", "f50"),
            NativeField("Embed", "f58", "su_CStringArray"),
            NativeField("Embed", "f80", "su_CStringArray"),
            NativeField("Embed", "fa8", "su_CStringArray"),
            NativeField("Embed", "fd0", "su_CStringArray"),
            NativeField("Embed", "ff8", "su_CStringArray"),
            NativeField("Embed", "f120", "su_CStringArray"),
            NativeField("Scalar", "f20", "i32"),
            NativeField("Scalar", "f24", "i32"),
            NativeField("Scalar", "f148", "u16"),
            NativeField("Node", "f10"),
            NativeField("Node", "f18"),
            NativeField(
                "Branch",
                "f148",
                BodyValue=(
                    NativeField("Embed", "f150", "moGtolItemDatum2022_c"),
                    NativeField("Embed", "f1c8", "moGtolItemDatum2022_c"),
                    NativeField("Embed", "f240", "moGtolItemDatum2022_c"),
                ),
                ModeValue="NotEquals",
            ),
            NativeField(
                "Array",
                "f2b8",
                "i32",
                BodyValue=(NativeField("Embed", "e", "moGtolItemIndicator_c"),),
                CountValue="n2b8",
                ModeValue="Positive",
            ),
        ),
    }
)
