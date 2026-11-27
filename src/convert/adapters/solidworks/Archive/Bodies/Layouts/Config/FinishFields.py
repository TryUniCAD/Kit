from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.AnnHelperFields import (
    KAnnHelperFields,
    KAnnHelperType,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.FormatAnnotationFields import (
    KFormatAnnotationFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# detail definitions and the two weld sides share this embedded class
KFinishType = "moSFDataHelper_c"

# the shared wire layout keeps both fonts and the two supplemental strings distinct
KFinishFields = MappingProxyType(
    {
        **KAnnHelperFields,
        "utCharFormat_c": KFormatAnnotationFields["utCharFormat_c"],
        KFinishType: (
            NativeField("Scalar", "f08", "i32"),
            NativeField("Text", "f10"),
            NativeField("Text", "f20"),
            NativeField("Text", "f18"),
            NativeField("Text", "f28"),
            NativeField("Text", "f30"),
            NativeField("Text", "f38"),
            NativeField("Text", "f40"),
            NativeField("Text", "f48"),
            NativeField("Text", "f50"),
            NativeField("Text", "f58"),
            NativeField("Scalar", "f68", "u8"),
            NativeField("Scalar", "f6c", "u8"),
            NativeField("Scalar", "f70", "u8"),
            NativeField("Scalar", "f74", "u8"),
            NativeField("Scalar", "f78", "i32"),
            NativeField("Scalar", "fa0", "u8"),
            NativeField("Scalar", "fa4", "u8"),
            NativeField("Scalar", "fa8", "u8"),
            NativeField("Scalar", "fac", "u8"),
            NativeField("Scalar", "fb0", "f64"),
            NativeField("Scalar", "fb8", "u8"),
            NativeField("Embed", "fc0", "utCharFormat_c"),
            NativeField("Scalar", "f120", "u8"),
            NativeField("Scalar", "f124", "u8"),
            NativeField("Embed", "f128", KAnnHelperType),
            NativeField("Scalar", "f7c", "i32"),
            NativeField("Scalar", "f80", "f64"),
            NativeField("Text", "f88"),
            NativeField("Text", "f90"),
            NativeField("Scalar", "f98", "i32"),
            NativeField("Scalar", "f9c", "i32"),
        ),
    }
)
