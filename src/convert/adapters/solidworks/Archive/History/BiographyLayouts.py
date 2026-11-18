from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# saved biography embeds ordered native telemetry records without allocating extra archive map entries
KBiographyLayouts = MappingProxyType(
    {
        "moStartEndRecord_c": (
            NativeField("Scalar", "f08", "u32"),
            NativeField("Scalar", "f0c", "u32"),
            NativeField("Scalar", "f10", "u32"),
            *(
                FieldValue
                for Index in range(6)
                for FieldValue in (
                    NativeField("Text", f"s{Index}"),
                    NativeField("Scalar", f"l{Index}", "i32"),
                    NativeField("Scalar", f"a{Index}", "u32"),
                    NativeField("Scalar", f"b{Index}", "u32"),
                )
            ),
        ),
        "moBiographyRecord_c": (
            NativeField("Scalar", "f08", "u32"),
            NativeField("Scalar", "f0c", "i32"),
            NativeField("Scalar", "f10", "i32"),
            NativeField("Scalar", "f14", "u32"),
            NativeField("Scalar", "f18", "u32"),
            NativeField("Scalar", "f1c", "u32"),
            NativeField("Scalar", "f20", "u32"),
            NativeField("Scalar", "f24", "u32"),
            NativeField("Scalar", "f28", "u32"),
            NativeField("Text", "f30"),
            NativeField("Scalar", "f38", "u16"),
            NativeField("Embed", "f40", "moStartEndRecord_c"),
            NativeField("Embed", "fe8", "moStartEndRecord_c"),
        ),
        "moBiography_c": (
            NativeField(
                "Array",
                "records",
                "i32",
                CountValue="n",
                BodyValue=(NativeField("Embed", "r", "moBiographyRecord_c"),),
            ),
        ),
    }
)
