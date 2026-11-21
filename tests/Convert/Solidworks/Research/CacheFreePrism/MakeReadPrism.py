from io import BytesIO
from convert import write_document as WriteDoc
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import (
    MakePlainDoc,
)


# the reader regression must consume actual public writer output from independent neutral dimensions without a native fixture
def MakeReadPrism(
    NameValue: str, WidthValue: float, HeightValue: float, DepthValue: float
) -> bytes:
    DocumentValue = MakePlainDoc(NameValue, WidthValue, HeightValue, DepthValue)
    OutputValue = BytesIO()
    ResultValue = WriteDoc(
        DocumentValue,
        OutputValue,
        destination_format="solidworks.sldprt",
        allow_carrier=False,
        values={"final_destination": "C:\\KitNoCacheTests\\" + NameValue + ".SLDPRT"},
    )
    BytesValue = OutputValue.getvalue()
    assert ResultValue.bytes_written == len(BytesValue) and BytesValue
    return BytesValue
