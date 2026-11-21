from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ViewLabelFields import (
    KViewLabelFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# detail definitions need each label subtype to retain its own wire suffix
KLabelAnnotationFields = MappingProxyType(
    {
        "moAuxLabelData_c": (
            NativeField("Base", "moDrViewLabelData_c"),
            NativeField("Scalar", "fc8", "i32"),
        ),
        "moDetailLabelData_c": (
            NativeField("Base", "moDrViewLabelData_c"),
            NativeField("Scalar", "fcc", "u32"),
            NativeField("Scalar", "fc8", "i32"),
        ),
        "moDrViewLabelData_c": KViewLabelFields,
        "moLabelDefs_c": (
            NativeField("Scalar", "f8", "i32"),
            NativeField("Scalar", "fc", "i32"),
            NativeField("Embed", "f18", "moDetailLabelData_c"),
            NativeField("Embed", "fe8", "moSectionLabelData_c"),
            NativeField("Embed", "f1e8", "moAuxLabelData_c"),
            NativeField("Embed", "f458", "utCharFormat_c"),
            NativeField("Embed", "f2b8", "moOrthoLabelData_c"),
            NativeField("Embed", "f388", "moMiscLabelData_c"),
        ),
        "moMiscLabelData_c": (
            NativeField("Base", "moDrViewLabelData_c"),
            NativeField("Scalar", "fc8", "i32"),
            NativeField("Scalar", "fcc", "i32"),
        ),
        "moOrthoLabelData_c": (
            NativeField("Base", "moDrViewLabelData_c"),
            NativeField("Scalar", "fc8", "i32"),
            NativeField("Scalar", "fcc", "i32"),
        ),
        "moSectionLabelData_c": (
            NativeField("Base", "moDrViewLabelData_c"),
            NativeField("Scalar", "fc8", "f64"),
            NativeField("Scalar", "fd0", "f64"),
            NativeField("Scalar", "fd8", "f64"),
            NativeField("Scalar", "fe0", "i32"),
            NativeField("Scalar", "fe4", "i32"),
            NativeField("Scalar", "fec", "i32"),
            NativeField("Scalar", "ff0", "i32"),
            NativeField("Scalar", "fe8", "i32"),
        ),
    }
)
