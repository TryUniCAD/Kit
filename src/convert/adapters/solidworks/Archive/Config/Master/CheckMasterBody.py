from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the supported resolved master has empty inherited lists and no mapped object links
def CheckMasterBody(NodeValue: ArchiveNode) -> None:
    Fields = NodeValue.FieldsValue
    if any(
        Fields.get(NameValue) is not None
        for NameValue in ("f18", "f78", "f258", "f2f0")
    ):
        raise BodyUnsupported(
            "SOLIDWORKS sheet metal master has an unsupported object link"
        )
    if (
        Fields.get("has_list68") != 0
        or "f68" in Fields
        or Fields.get("f60") != {"list": {"n": 0, "items": []}, "tail": 0}
        or Fields.get("f358") != []
    ):
        raise BodyUnsupported("SOLIDWORKS sheet metal master requires empty body lists")
    if any(
        NameValue in Fields for NameValue in ("cond1_a", "cond1_b", "f200", "pe_noise")
    ):
        raise BodyUnsupported(
            "SOLIDWORKS sheet metal master has unsupported resolved flags"
        )
