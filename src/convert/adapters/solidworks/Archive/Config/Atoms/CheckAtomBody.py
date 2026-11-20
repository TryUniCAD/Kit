from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the measured ordinary atoms have no separate names visual properties or list entries
def CheckAtomBody(NodeValue: ArchiveNode) -> None:
    Fields = NodeValue.FieldsValue
    if (
        Fields["f18"] is not None
        or Fields["f78"] is not None
        or Fields["has_list68"] != 0
    ):
        raise BodyUnsupported("unqualified SOLIDWORKS atom concept links")
    Resolved = CastValue(dict[str, object], Fields.get("f60"))
    if Resolved != {"list": {"n": 0, "items": []}, "tail": 0}:
        raise BodyUnsupported("unqualified SOLIDWORKS atom resolved list")
