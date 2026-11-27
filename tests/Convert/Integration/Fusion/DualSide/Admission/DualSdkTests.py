from hashlib import sha256 as HashBytes

from pytest import mark as MarkTests, raises as RaisesError

from convert import open_document as OpenDocument
from interchange.geometry.Models.Transform import Transform
from tests.Convert.Integration.Fusion.DualSide.Admission.CheckAdmitDoc import (
    CheckAdmitDoc,
)
from tests.Convert.Integration.Fusion.DualSide.Admission.ReadAdmitCases import (
    ReadAdmitCases,
)
from tests.Convert.Integration.Fusion.DualSide.DualCase import DualCase
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases


# every committed independent edit restoration and held out xy state crosses the public sdk boundary
@MarkTests.parametrize(
    "Sample", ReadAdmitCases(), ids=[Value.Identity for Value in ReadAdmitCases()]
)
def CheckDualAdmit(Sample: DualCase) -> None:
    assert HashBytes(Sample.Source.read_bytes()).hexdigest() == Sample.Digest
    Document = OpenDocument(Sample.Source, strict=True)
    CheckAdmitDoc(Document, Sample)


# solved geometry in a different frame cannot bypass existing native placement qualification
@MarkTests.parametrize(
    "Sample", tuple(Value for Value in ReadDualCases() if Value.Frame != Transform())
)
def CheckDualFrame(Sample: DualCase) -> None:
    with RaisesError(ValueError):
        _ = OpenDocument(Sample.Source, strict=True)
