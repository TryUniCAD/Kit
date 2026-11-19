from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current display note fields follow their actual inherited display item and typed pointer owners
KNoteHead = (
    NativeField("Base", "moDisplayItem_c.Serialize"),
    NativeField("Scalar", "f644", "u16"),
    NativeField("Scalar", "f648", "u16"),
    NativeField("Scalar", "f64c", "u16"),
    NativeField("Embed", "f628", "mgVector_c.restore"),
    NativeField("Scalar", "f630", "f64"),
    NativeField("Scalar", "f690", "i32"),
    NativeField("Scalar", "f694", "i32"),
    NativeField("Node", "f6a0", "suHyperlink_c"),
    NativeField("Text", "f658"),
    NativeField("Text", "f660"),
    NativeField("Text", "f668"),
    NativeField("Node", "f6b8", "su_CMapStringToString"),
    NativeField("Node", "f590", "moStackedNoteData_c"),
    NativeField(
        "Array",
        "f768",
        "i32",
        BodyValue=(NativeField("Scalar", "v", "u32"),),
        CountValue="n768",
        ModeValue="Positive",
    ),
    NativeField("Node", "f5a0", "moChainComponent_c"),
    NativeField("Scalar", "f698", "f64"),
)
