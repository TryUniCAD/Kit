from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Definition.Fields.ScalarFields import (
    MakeScalarRows,
)

# current paragraph framing keeps narrowed alignment words and all independently version gated numeric fields in native order
KNoteParagraphFields = (
    NativeField("Scalar", "f00", "u16"),
    *MakeScalarRows("f64", "f08 f10 f18"),
    *MakeScalarRows("u16", "f20 f24"),
    NativeField("Text", "f28"),
    NativeField("Scalar", "f30", "i32"),
    NativeField("Scalar", "f34", "u32"),
    NativeField("Scalar", "f38", "i32"),
    *MakeScalarRows("f64", "f40 f48"),
    NativeField("Scalar", "f50", "i32"),
    *MakeScalarRows("f64", "f58 f60"),
    *MakeScalarRows("i32", "f68 f6c"),
)
