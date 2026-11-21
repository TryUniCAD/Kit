from typing import cast as CastValue

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
    CheckMasterList(Fields.get("f60"))
    if Fields.get("has_list68") != 0 or "f68" in Fields or Fields.get("f358") != []:
        raise BodyUnsupported("SOLIDWORKS sheet metal master requires empty body lists")
    if any(
        NameValue in Fields for NameValue in ("cond1_a", "cond1_b", "f200", "pe_noise")
    ):
        raise BodyUnsupported(
            "SOLIDWORKS sheet metal master has unsupported resolved flags"
        )


# an alternate empty count width must be distinguished from a populated list
def CheckMasterList(ListValue: object) -> None:
    RowsValue = (
        CastValue(dict[str, object], ListValue).get("list")
        if isinstance(ListValue, dict)
        else None
    )
    if isinstance(RowsValue, dict) and "n#width" in RowsValue:
        raise BodyUnsupported(
            "SOLIDWORKS sheet metal master has a noncanonical inherited list count width"
        )
    if ListValue != {"list": {"n": 0, "items": []}, "tail": 0}:
        raise BodyUnsupported("SOLIDWORKS sheet metal master requires empty body lists")
