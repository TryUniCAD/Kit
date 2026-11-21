from typing import cast as CastValue

from interchange.serialization.EncodeData import ToData
from tests.Convert.Solidworks.Research.Construction.Part.BlindCaseInput import (
    BlindCaseInput,
)
from tests.Convert.Solidworks.Research.Construction.RectangleAnchors.MakeCornerDoc import (
    MakeCornerDoc,
)


# neutral discovery jobs expose geometry dimensions and annotation positions without interpreting a vendor saved document
def CornerRequest(
    NameValue: str,
    LengthValue: float,
    WidthValue: float,
    DepthValue: float,
    IsVariant: bool = False,
) -> dict[str, object]:
    RequestValue = BlindCaseInput(NameValue, IsVariant)
    RequestValue["document"] = CastValue(
        object, ToData(MakeCornerDoc(NameValue, LengthValue, WidthValue, DepthValue))
    )
    RequestValue["rectangle_dimensions"] = {
        "width_text_m": [LengthValue * 0.00035, -0.0067],
        "height_text_m": [
            LengthValue * 0.001 + 0.0082,
            WidthValue * 0.00061,
        ],
        "route_centerline": IsVariant,
    }
    return RequestValue
