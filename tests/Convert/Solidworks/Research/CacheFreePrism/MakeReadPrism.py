from io import BytesIO

from pytest import raises as RaisesError

from convert import write_document as WriteDoc
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import (
    MakePlainDoc,
)


# independent neutral dimensions must feed the cold reader through actual sdk archive construction
def MakeReadPrism(
    NameValue: str, WidthValue: float, HeightValue: float, DepthValue: float
) -> bytes:
    DocumentValue = MakePlainDoc(NameValue, WidthValue, HeightValue, DepthValue)
    OutputValue = BytesIO()
    Values = {
        "final_destination": "C:\\KitNoCacheTests\\" + NameValue + ".SLDPRT",
        "require_native_transfers": True,
    }
    Candidate = PrepareNative(
        DocumentValue, OutputValue, 1794973072, WriteOptions(values=Values)
    )
    assert Candidate.BytesValue and OutputValue.getvalue() == b""
    with RaisesError(ValueError, match="offline native measurement receipt"):
        _ = WriteDoc(
            DocumentValue,
            OutputValue,
            destination_format="solidworks.sldprt",
            allow_carrier=False,
            values=Values,
        )
    assert OutputValue.getvalue() == b"" and OutputValue.tell() == 0
    return Candidate.BytesValue
