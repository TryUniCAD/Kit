from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Container.CheckArcFrames import CheckArcFrames
from convert.adapters.solidworks.Container.Container import (
    KArchiveOffset,
    SldprtArchive,
)
from convert.adapters.solidworks.Core.Adapter import (
    KSourceBytesKey,
    KSourceShaTwoFiveSixKey,
)
from convert.adapters.solidworks.Core.Preparation.Chamfers.CheckChmfSha import (
    CheckChmfSha,
)
from convert.adapters.solidworks.Core.Preparation.Chamfers.StripChmfSnap import (
    StripChmfSnap,
)
from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdDoc import (
    ReadColdDoc,
)
from interchange.document.Behavior.DocumentIo import ToJson
from interchange.document.Models.DocumentModel import CadDocument


# all modeled records are compared after only the original transport identity is authenticated
def CheckChmfSnap(
    Document: CadDocument,
    Candidate: PartCandidate,
    Recipe: SelfFileInput,
    Attachment: tuple[bytes, SldprtArchive] | None,
) -> CadDocument:
    if Attachment is None:
        CheckChmfSha(Document.source.sha256, Candidate)
    else:
        BlobValue, Original = Attachment
        Streams = Original.streams
        if Streams != Candidate.StreamsValue or tuple(Streams) != tuple(
            Candidate.StreamsValue
        ):
            raise ValueError(
                "cold chamfer JSON source logical streams differ from its regenerated part"
            )
        if BlobValue[:KArchiveOffset] != Candidate.BytesValue[:KArchiveOffset]:
            raise ValueError(
                "cold chamfer JSON source header differs from its regenerated part"
            )
        CheckArcFrames(BlobValue, Original)
    Expected = ReadColdDoc(Document.source.path, Candidate.BytesValue)
    SourceSha = Document.source.sha256
    Expected = ReplaceValue(
        Expected,
        source=ReplaceValue(Expected.source, sha256=SourceSha),
        metadata=dict(Expected.metadata) | {KSourceShaTwoFiveSixKey: SourceSha},
    )
    if Attachment is None:
        CompareDoc, Expected = Document, StripChmfSnap(Expected, Recipe)
    else:
        CompareDoc, Expected = WithoutChmfWire(Document), WithoutChmfWire(Expected)
    if Expected.brep is None or ToJson(CompareDoc, IndentSize=None) != ToJson(
        Expected, IndentSize=None
    ):
        raise ValueError("cold chamfer JSON readback differs from its regenerated part")
    return Document if Attachment is None else StripChmfSnap(Document, Recipe)


# an authenticated transport attachment need not be serialized during the complete record comparison
def WithoutChmfWire(Document: CadDocument) -> CadDocument:
    Metadata = dict(Document.metadata)
    del Metadata[KSourceBytesKey]
    return ReplaceValue(Document, metadata=Metadata)
