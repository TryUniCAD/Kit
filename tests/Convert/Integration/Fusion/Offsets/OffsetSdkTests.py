from hashlib import sha256 as HashBytes

from pytest import mark as MarkTests

from convert import open_document as OpenDocument
from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Integration.Fusion.Offsets.CheckOffsetRead import CheckOffsetRead
from tests.Convert.Integration.Fusion.Offsets.OffsetCase import OffsetCase
from tests.Convert.Integration.Fusion.Offsets.ReadOffsetCases import ReadOffsetCases


# public sdk reads must survive neutral serialization without erasing start placement
@MarkTests.parametrize("Sample", ReadOffsetCases())
def CheckOffsetSdk(Sample: OffsetCase) -> None:
    assert HashBytes(Sample.Source.read_bytes()).hexdigest() == Sample.Digest
    Document = OpenDocument(Sample.Source)
    CheckOffsetRead(Document, Sample)
    Restored = CadDocument.from_json(Document.to_json())
    assert Restored == Document
    CheckOffsetRead(Restored, Sample)
