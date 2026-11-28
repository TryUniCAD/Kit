from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# component references retain the shared prefix and actual alias branch before entity and extended file tags
KNoteBEntFields = (
    NativeField("Base", "moCompRef_c"),
    NativeField("Scalar", "alias_present", "u8"),
    NativeField(
        "Branch",
        "alias_present",
        ModeValue="Nonzero",
        BodyValue=(NativeField("Text", "f08"),),
    ),
    NativeField("Node", "fe8", "moBEntRef_c"),
    NativeField("Node", "ff0", "moExtObject_c"),
)

# both actual composite flags control the optional pair independently from the counted ordinary object row array
KNoteEdgeLinks = (
    "And",
    (
        "compare",
        ("NotEq",),
        ("BitAnd", ("lookup", ("scope",), ("literal", "f188")), ("literal", 6)),
        ("literal", 6),
    ),
    (
        "compare",
        ("NotEq",),
        ("BitAnd", ("lookup", ("scope",), ("literal", "f188")), ("literal", 8)),
        ("literal", 0),
    ),
)

# current composite edge fields use the original point operators and fixed signed count before optional linked composites
KNoteCompositeFields = (
    NativeField("Base", "moCompBEntRef_c"),
    NativeField("Scalar", "f188", "i32"),
    NativeField("Embed", "f158", "mgPoint_c.operator>>"),
    NativeField("Embed", "f170", "mgPoint_c.operator>>"),
    NativeField("Scalar", "f18c", "u32"),
    NativeField("Array", "f130", "i32", BodyValue=(NativeField("Node", "object"),)),
    NativeField(
        "Branch",
        "f188",
        ModeValue="Expression",
        ExpressionValue=KNoteEdgeLinks,
        BodyValue=(
            NativeField("Node", "f190", "moCompCompositeEdge_c"),
            NativeField("Node", "f198", "moCompCompositeEdge_c"),
        ),
    ),
)
