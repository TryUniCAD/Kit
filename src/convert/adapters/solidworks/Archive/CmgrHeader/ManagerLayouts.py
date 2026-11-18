from types import MappingProxyType
from convert.adapters.solidworks.Archive.Bodies.Layouts.ContainerFields import (
    KContainerFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current lightweight configuration headers retain native store order and share actual archive list framing with the body codecs
KManagerLayouts = MappingProxyType(
    {
        "suObList": KContainerFields["suObList"],
        "dmConfigHeader_c": (
            NativeField("Scalar", "f08", "i32"),
            NativeField("Text", "f10"),
            NativeField("Scalar", "f30", "i32"),
            NativeField("Scalar", "f38", "u32"),
            NativeField("Text", "f18"),
            NativeField("Scalar", "f34", "i32"),
            NativeField("Scalar", "f40", "i32"),
            NativeField("Text", "f20"),
            NativeField("Text", "f28"),
            NativeField("Scalar", "f44", "i32"),
            NativeField("Scalar", "f48", "i32"),
            NativeField("Scalar", "f50", "u32"),
            NativeField("Scalar", "f4c", "u32"),
        ),
        "dmConfigMgrHeader_c": (
            NativeField("Embed", "f08", "suObList"),
            NativeField("Scalar", "f60", "u32"),
            NativeField("Scalar", "f68", "i32"),
        ),
    }
)

# native runtime descriptors establish both concrete manager header schemas without borrowing a saved declaration
KManagerSchemas = MappingProxyType(
    {"dmConfigMgrHeader_c": (1,), "dmConfigHeader_c": (1,)}
)
