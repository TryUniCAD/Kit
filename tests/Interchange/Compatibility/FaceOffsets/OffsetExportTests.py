from dataclasses import replace as CopyData
from io import BytesIO
import pytest as Pytest

from convert.api.ApiWrite import WriteDocument
from convert.adapters.json.Adapter import JsonAdapter
from tests.Interchange.Compatibility.FaceOffsets.BuildOffsetDoc import BuildOffsetDoc


# an offset schema alone cannot attest that its retained stock geometry is an evaluated export result
@Pytest.mark.parametrize("Amount", (-2.7, 0.0, 4.3))
def CheckOffsetGate(Amount: float) -> None:
    Document = BuildOffsetDoc()
    Parameter = CopyData(
        Document.parameters[-1],
        value=CopyData(Document.parameters[-1].value, value=Amount),
    )
    Document = CopyData(Document, parameters=(*Document.parameters[:-1], Parameter))
    Stream = BytesIO()
    with Pytest.raises(ValueError, match="no qualified geometry evaluator"):
        _ = WriteDocument(Document, Stream, DestFormat="interchange.json")
    assert Stream.getvalue() == b""
    with Pytest.raises(ValueError, match="no qualified geometry evaluator"):
        _ = JsonAdapter().Write(Document, Stream)
    assert Stream.getvalue() == b""
