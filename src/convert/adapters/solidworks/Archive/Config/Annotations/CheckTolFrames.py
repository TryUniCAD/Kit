from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported


# inherited map references cannot acquire tolerance ownership through a null only profile
def CheckTolFrames(FieldsValue: Mapping[str, object]) -> None:
    RowsValue = FieldsValue.get("f08")
    if not isinstance(RowsValue, list) or FieldsValue.get("n08") != len(RowsValue):
        raise BodyUnsupported(
            "SOLIDWORKS tolerance helper requires a nonnegative frame count"
        )
    for RowValue in RowsValue:
        FrameValue = RowValue["e"]
        if FrameValue["f10"] is not None or FrameValue["f18"] is not None:
            raise BodyUnsupported(
                "SOLIDWORKS tolerance frame has an unqualified reference owner"
            )
        if FrameValue["n2b8"] != 0:
            raise BodyUnsupported(
                "SOLIDWORKS tolerance frame has an unqualified indicator count"
            )
