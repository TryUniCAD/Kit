from ntpath import join as JoinPath
from typing import cast as CastValue
from interchange.serialization.EncodeData import ToData
from tests.Convert.Solidworks.Research.Construction.Part.BlindCaseInput import (
    BlindCaseInput,
)
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import (
    MakePlainDoc,
)


# recursive constructor probes need independently authored physical dimensions while preserving the actual neutral document and explicit supported part settings
def NestedPartInput(
    NameValue: str,
    Dimensions: tuple[float, float, float],
    OutputRoot: str,
) -> dict[str, object]:
    InputValue = BlindCaseInput(NameValue, False)
    InputValue["document"] = CastValue(
        object, ToData(MakePlainDoc(NameValue, *Dimensions))
    )
    Settings = CastValue(dict[str, object], InputValue["settings"])
    OutputValue = CastValue(dict[str, object], Settings["output"])
    OutputValue["path_name"] = JoinPath(OutputRoot, NameValue + ".SLDPRT")
    return InputValue
