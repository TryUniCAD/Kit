from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Mates.RequireCylEnds import RequireCylEnds
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# the current concentric archive grammar covers ordinary alignment and rotation lock without a position tail
def RequireCylMate(NodeValue: ArchiveNode) -> None:
    FieldsValue = NodeValue.FieldsValue
    if (
        FieldInt(FieldsValue, "f3b4") not in (1, 2)
        or FieldInt(FieldsValue, "f4b8") not in (0, 1)
        or FieldInt(FieldsValue, "f4c4") != -1
    ):
        raise BodyUnsupported("concentric alignment or position is unqualified")
    RequireCylEnds(FieldsValue)
