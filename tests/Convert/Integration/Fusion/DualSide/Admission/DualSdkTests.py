from hashlib import sha256 as HashBytes

from pytest import mark as MarkTests

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
from tests.Convert.Integration.Fusion.DualSide.Admission.CheckWorldDoc import (
    CheckWorldDoc,
)


# every committed independent edit restoration and held out xy state crosses the public sdk boundary
@MarkTests.parametrize(
    "Sample", ReadAdmitCases(), ids=[Value.Identity for Value in ReadAdmitCases()]
)
def CheckDualAdmit(Sample: DualCase) -> None:
    assert HashBytes(Sample.Source.read_bytes()).hexdigest() == Sample.Digest
    Document = OpenDocument(Sample.Source, strict=True)
    CheckAdmitDoc(Document, Sample)


# independently qualified source frames must retain their actual support and world solid geometry
@MarkTests.parametrize(
    "Sample", tuple(Value for Value in ReadDualCases() if Value.Frame != Transform())
)
def CheckDualFrame(Sample: DualCase) -> None:
    Document = OpenDocument(Sample.Source, strict=True)
    CheckAdmitDoc(Document, Sample)
    CheckWorldDoc(Document, Sample)
