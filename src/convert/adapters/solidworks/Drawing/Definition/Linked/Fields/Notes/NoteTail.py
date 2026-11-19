from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current note tail preserves favorite BOM thread map and numeric state without applying native load fixups
KNoteTail = (
    NativeField("Text", "f6d8"),
    NativeField("Node", "f6e0"),
    NativeField("Scalar", "f640", "u16"),
    NativeField("Node", "f5b0", "moBomFeat_c"),
    NativeField("Scalar", "f5b8", "i32"),
    NativeField("Scalar", "f5bc", "i32"),
    NativeField("Scalar", "f710", "f64"),
    NativeField("Scalar", "f5c0", "i32"),
    NativeField("Scalar", "f770", "u32"),
    NativeField("Scalar", "f784", "i32"),
    NativeField("Scalar", "f788", "i32"),
    NativeField("Scalar", "f78c", "i32"),
    NativeField("Node", "f790", "moCompCThread_c"),
    NativeField("Node", "f6c0", "su_CMapStringToInt"),
)
