from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
    RequireRecord,
)


# the populated manager mode must bind an ordinary local atom and activation mark
def CheckImpScope(VersionValue: int, OwnerValue: ArchiveNode) -> None:
    FieldsValue = OwnerValue.FieldsValue
    try:
        ManagerValue = RequireRecord(FieldsValue.get("fd88"))
        MarkValue = RequireNode(FieldsValue.get("fe38"), "moPMarkRecord_c")
        (EntryValue,) = ReadRows(ManagerValue.get("atoms"))
        AtomValue = RequireNode(EntryValue.get("o"), "moAtom_c")
        if (
            VersionValue != 19000
            or FieldInt(FieldsValue, "f1010") != 1
            or FieldInt(MarkValue.FieldsValue, "f18") <= 0
            or FieldInt(ManagerValue, "n6c") != 1
            or FieldInt(ManagerValue, "fa8") != VersionValue
            or FieldInt(ManagerValue, "f260") != FieldInt(AtomValue.FieldsValue, "f140")
        ):
            raise ValueError("local import manager fields differ")
    except (TypeError, ValueError) as ErrorValue:
        raise BodyUnsupported(
            "unsupported ordinary local import manager"
        ) from ErrorValue
