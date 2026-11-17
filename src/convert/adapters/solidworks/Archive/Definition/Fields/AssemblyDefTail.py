from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Definition.Fields.ScalarFields import (
    MakeScalarRows,
)

# assembly save-as-part preferences remain inline and use the native field ordering
KAssemblyDefTail = MappingProxyType(
    {
        "uiAssemblyDoc_c.Serialize.own": (
            *MakeScalarRows("i32", "f1840 f19c8"),
            NativeField("Text", "f1a38"),
            NativeField("Text", "f1a40"),
            *MakeScalarRows("i32", "f1a48 f19b0"),
            NativeField("Scalar", "f19b8", "f64"),
            NativeField("Scalar", "f19c0", "i32"),
            NativeField("Embed", "f1b48", "uiSaveAssemblyAsPartSettings_c.Serialize"),
            NativeField("Scalar", "f1afc", "i32"),
        ),
        "uiSaveAssemblyAsPartSettings_c.Serialize": (
            *MakeScalarRows("i32", "f08 f0c"),
            NativeField("Scalar", "f10", "f64"),
            NativeField("Scalar", "f18", "i32"),
            NativeField("Scalar", "f20", "f64"),
            *MakeScalarRows("i32", "f28 f30 f34 f2c f38 f3c"),
        ),
    }
)
