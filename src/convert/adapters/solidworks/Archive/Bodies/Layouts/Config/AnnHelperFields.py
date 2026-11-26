from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# several detailing owners embed the same annotation helper body
KAnnHelperType = "moAnnotationDataHelper_c"

# the annotation helper owns its font and both independently stored leader groups
KAnnHelperFields = MappingProxyType(
    {
        KAnnHelperType: (
            NativeField("Scalar", "f68", "i32"),
            NativeField("Scalar", "f6c", "i32"),
            NativeField("Scalar", "f70", "i32"),
            NativeField("Scalar", "f74", "i32"),
            NativeField("Scalar", "f78", "u8"),
            NativeField("Embed", "f08", "utCharFormat_c"),
            NativeField("Scalar", "f7c", "u8"),
            NativeField("Scalar", "f80", "i32"),
            NativeField("Scalar", "f88", "f64"),
            NativeField("Scalar", "f90", "i32"),
            NativeField("Scalar", "f94", "u8"),
            NativeField("Scalar", "f98", "i32"),
            NativeField("Scalar", "fa0", "f64"),
            NativeField("Scalar", "fa8", "i32"),
        )
    }
)
