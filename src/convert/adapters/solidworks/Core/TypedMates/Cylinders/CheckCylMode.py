from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Core.TypedMates.CheckMateMode import CheckMateMode


# unsolved or linked position variants must not be represented as an ordinary solved cylinder relationship
def CheckCylMode(NodeValue: ArchiveNode) -> None:
    CheckMateMode(NodeValue)
    FieldsValue = NodeValue.FieldsValue
    if (
        FieldInt(FieldsValue, "f3b8") != 1
        or FieldInt(FieldsValue, "f0c") != 0x100
        or FieldInt(FieldsValue, "f4b8") not in (0, 1)
        or FieldInt(FieldsValue, "f4c4") != -1
        or FieldsValue.get("f488") != ""
        or FieldsValue.get("f490") != ""
    ):
        raise ValueError(
            "concentric mate is outside the ordinary solved position profile"
        )
