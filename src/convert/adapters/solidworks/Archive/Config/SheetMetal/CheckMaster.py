from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the ordinary direct master has no inherited links or separately owned body rows
def CheckMaster(NodeValue: ArchiveNode) -> None:
    Fields = NodeValue.FieldsValue
    if (
        any(
            Fields[NameValue] is not None
            for NameValue in ("f18", "f78", "f258", "f2f0")
        )
        or Fields["has_list68"] != 0
        or Fields["f60"]
        not in (
            {"list": {"n": 0, "items": []}, "tail": 0},
            {"list": {"n": 0, "n#width": 6, "items": []}, "tail": 0},
        )
    ):
        raise BodyUnsupported("unqualified SOLIDWORKS sheet metal master links")
