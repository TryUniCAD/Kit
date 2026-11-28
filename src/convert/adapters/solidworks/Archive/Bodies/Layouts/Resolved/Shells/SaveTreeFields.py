from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# a native save keeps the real history shortcuts and ordinary detail folders
KSaveTreeFields = MappingProxyType(
    {
        "moHistoryFeatItemData_c": (
            NativeField("Base", "moNode_c"),
            NativeField("Node", "f48", "moCompFeature_c"),
        ),
        "moFtrFolder_c": (
            NativeField("Base", "moFolder_c"),
            NativeField("Node", "f388", "moFtrFolder_c"),
            NativeField("Scalar", "f37c", "i32"),
            NativeField("Scalar", "f394", "i32"),
            NativeField(
                "Virtual",
                "",
                BodyValue=(NativeField("Scalar", "f378", "i32"),),
                ModeValue="Flag",
                MaskValue=2624,
            ),
            NativeField("Scalar", "f39c", "i32"),
        ),
        "moNotesAreaFtrFolder_c": (NativeField("Base", "moFtrFolder_c"),),
    }
)

# these native roles select the appropriate existing node and folder callbacks
KSaveTreeVirts = MappingProxyType(
    {
        ("moHistoryFeatItemData_c", 1000): None,
        ("moHistoryFeatItemData_c", 1016): True,
        ("moHistoryFeatItemData_c", 1208): "moNode_c.SerializeLWData",
        ("moHistoryFeatItemData_c", 1216): None,
        ("moNotesAreaFtrFolder_c", 1000): "moFeature_c.SerializeXmlData",
        ("moNotesAreaFtrFolder_c", 1016): True,
        ("moNotesAreaFtrFolder_c", 1208): "moConcept_c.SerializeLWData",
        ("moNotesAreaFtrFolder_c", 1216): "moConcept_c.SerializeResolvedData",
        ("moNotesAreaFtrFolder_c", 2624): True,
    }
)
