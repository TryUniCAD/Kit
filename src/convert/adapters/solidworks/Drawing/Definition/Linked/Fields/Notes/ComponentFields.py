from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.EdgeFields import (
    KEdgeGate,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.ComponentPrefixes import (
    KNoteBEntFields,
    KNoteCompositeFields,
)


# these component bodies require the actual ordinary drawing owner and exclude alternate entity restoration context
def GateComponents(FieldsValue: tuple[NativeField, ...]) -> tuple[NativeField, ...]:
    return (
        NativeField(
            "Branch",
            "",
            BodyValue=FieldsValue,
            OtherValue=(
                NativeField("Fail", "component edge special drawing archive context"),
            ),
            ModeValue="Expression",
            ExpressionValue=KEdgeGate,
        ),
    )


# ordinary drawing mode keeps four actual persistent reference words after the common composite edge rather than the part suffix
KNoteComponentFields = MappingProxyType(
    {
        "moCompBEntRef_c": GateComponents(KNoteBEntFields),
        "moCompCompositeEdge_c": GateComponents(KNoteCompositeFields),
        "moCompEdge_c": GateComponents(
            (
                NativeField("Base", "moCompCompositeEdge_c"),
                NativeField("Scalar", "f1b4", "i32"),
                NativeField("Scalar", "f1b8", "i32"),
                NativeField("Scalar", "f1bc", "i32"),
                NativeField("Scalar", "f1c0", "i32"),
            )
        ),
    }
)
