from typing import cast as CastValue

from interchange.serialization.EncodeData import ToData
from tests.Convert.Solidworks.Research.Construction.Part.BlindCaseInput import (
    BlindCaseInput,
)
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import (
    MakePlainDoc,
)


# independent geometry sizes must reach the public presentation projection through actual generated archive bytes
def MakeTreeInput(
    NameValue: str, WidthValue: float, HeightValue: float, DepthValue: float
) -> dict[str, object]:
    Request = BlindCaseInput(NameValue, False)
    Request["document"] = CastValue(
        object,
        ToData(
            MakePlainDoc(
                NameValue, WidthValue * 1000, HeightValue * 1000, DepthValue * 1000
            )
        ),
    )
    return Request
