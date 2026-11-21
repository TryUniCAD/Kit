from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.AnnHelperFields import (
    KAnnHelperFields,
    KAnnHelperType,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# tolerance helper framing owns the native frame rows and preceding formats
KTolHeadFields = (
    NativeField(
        "Array",
        "f08",
        "i32",
        BodyValue=(NativeField("Embed", "e", "moGTolDlgDataFrame_c"),),
        CountValue="n08",
        ModeValue="Positive",
    ),
    NativeField("Scalar", "f30", "i32"),
    NativeField("Scalar", "f34", "i32"),
    NativeField("Text", "f38"),
    NativeField("Scalar", "f40", "u8"),
    NativeField("Scalar", "f4c", "u8"),
    NativeField("Scalar", "f50", "u8"),
    NativeField("Scalar", "f54", "u8"),
    NativeField("Scalar", "f58", "i32"),
    NativeField("Scalar", "f68", "u8"),
    NativeField("Text", "f70"),
    NativeField("Text", "f78"),
    NativeField("Scalar", "f80", "u8"),
    NativeField("Text", "f88"),
    NativeField("Text", "f90"),
    NativeField("Scalar", "f98", "u8"),
)

# the remaining tolerance controls retain their typed format after frame traversal
KTolTailFields = (
    NativeField("Text", "f60"),
    NativeField("Scalar", "f9c", "u8"),
    NativeField("Scalar", "fac", "u8"),
    NativeField("Scalar", "f110", "u8"),
    NativeField("Scalar", "f114", "u8"),
    NativeField("Embed", "fb0", "utCharFormat_c"),
    NativeField("Embed", "f118", KAnnHelperType),
    NativeField("Scalar", "fa0", "u8"),
    NativeField("Scalar", "f44", "u8"),
    NativeField("Scalar", "f48", "u8"),
    NativeField("Scalar", "fa4", "u8"),
    NativeField("Scalar", "fa8", "u8"),
    NativeField("Scalar", "f1e0", "u8"),
)

# tolerance frames and character format helpers must keep their distinct embedded owners
KTolHelperFields = MappingProxyType(
    {
        **KAnnHelperFields,
        "moGTolDataHelper_c": (*KTolHeadFields, *KTolTailFields),
    }
)
