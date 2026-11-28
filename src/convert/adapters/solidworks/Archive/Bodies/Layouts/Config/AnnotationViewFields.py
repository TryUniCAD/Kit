from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current native field order supplies both directions without saved document values
KAnnotationViewFields = MappingProxyType(
    {
        "moAnnotationView_c": (
            NativeField("Base", "moView_c"),
            NativeField("Scalar", "f3d8", "i32"),
            NativeField("Node", "f3d0"),
            NativeField("Node", "f3e8#0", OtherName="f3e8"),
            NativeField("Scalar", "f3f0", "i32"),
            NativeField("Scalar", "f3e0", "f64"),
            NativeField("Node", "f3e8"),
            NativeField("Scalar", "f3f4", "i32"),
            NativeField("Scalar", "f3f8", "i32"),
            NativeField("Node", "f2f0"),
            NativeField("Scalar", "f3fc", "i32"),
            NativeField("Scalar", "f408", "i32"),
            NativeField("Scalar", "f400", "i32"),
            NativeField("Scalar", "f404", "i32"),
        ),
    }
)
