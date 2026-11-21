from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported


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
