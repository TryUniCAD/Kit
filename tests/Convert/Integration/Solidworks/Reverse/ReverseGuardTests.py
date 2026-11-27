from io import BytesIO

from pytest import mark as TestMark, raises as RaisesError

from convert.api import open_document as OpenDocument
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from tests.Convert.Integration.Solidworks.Reverse.MakeBadReverse import MakeBadReverse


# direction and ownership corruption must refuse a complete archive instead of returning a guessed solid
@TestMark.parametrize("ModeName", ("direction", "owner", "support"))
def CheckBadReverse(ModeName: str) -> None:
    DataValue = MakeBadReverse(ModeName)
    with RaisesError(SldprtFormat, match="no readable Parasolid payload"):
        _ = OpenDocument(
            BytesIO(DataValue), source_format="solidworks.sldprt", strict=True
        )
