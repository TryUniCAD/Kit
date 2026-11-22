from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the saved resolved body reaches these ordinary native owner fields in their verified order
KSavedFolderFields = MappingProxyType(
    {
        "moNotesAreaFtrFolder_c": (NativeField("Base", "moFtrFolder_c"),),
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
    }
)
