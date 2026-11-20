from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.ObListFields import (
    KObListFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.CmgrHeader.ManagerSchemas import (
    KConfigHdrClass,
    KManagerClass,
)

# current lightweight configuration headers retain native store order and share actual archive list framing with the body codecs
KManagerLayouts = MappingProxyType(
    {
        "suObList": KObListFields,
        KConfigHdrClass.NameValue: (
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
        KManagerClass.NameValue: (
            NativeField("Embed", "f08", "suObList"),
            NativeField("Scalar", "f60", "u32"),
            NativeField("Scalar", "f68", "i32"),
        ),
    }
)
