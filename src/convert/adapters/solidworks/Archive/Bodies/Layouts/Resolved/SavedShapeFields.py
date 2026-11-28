from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the saved resolved body reaches these ordinary native owner fields in their verified order
KSavedShapeFields = MappingProxyType(
    {
        "moBBoxCenterData_c": (
            NativeField("Scalar", "f08", "i32"),
            NativeField("Embed", "f10", "mgPoint_c.restore"),
            NativeField("Scalar", "f28", "f64"),
        ),
        "moBodyChooser_c": (
            NativeField("Embed", "f48", "rf.suObArray"),
            NativeField("Node", "f68", "moAtomFeature_c"),
        ),
        "moPerBodyChooserData_c": (
            NativeField("Embed", "f08", "rf.suObArray"),
            NativeField("Embed", "f28", "rf.suObArray"),
            NativeField("Embed", "f48", "rf.suObArray"),
            NativeField("Scalar", "f68", "i32"),
            NativeField("Scalar", "f6c", "i32"),
            NativeField("Embed", "f78", "su_CDWordArray"),
            NativeField("Scalar", "f70", "i32"),
        ),
    }
)
