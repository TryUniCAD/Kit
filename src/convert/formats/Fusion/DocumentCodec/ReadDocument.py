from collections.abc import Callable

from convert.formats.Fusion.BrepCodec.ReadHistory import ReadHistory
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.Model.DocumentBody import DocumentBody
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Records.MakeDocProfile import MakeDocProfile
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSegment import ReadDocSegment
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire


def ReadDocument(
    Payload: bytes, InflateZstd: Callable[[bytes, int], bytes] | None = None
) -> DocumentModel:
    Container = ReadContainer(Payload, InflateZstd)
    Schemas = ReadDocSchemas()
    Metadata = tuple(
        ReadMetaWire(Stream.Metadata, Segment=SlotValue.Segment)
        for Stream, SlotValue in zip(
            Container.Streams, Container.Asset.Segments, strict=True
        )
    )
    Segments = tuple(
        ReadDocSegment(
            Stream, MetaValue, MakeDocProfile(Schemas, Metadata, Stream.SegmentId)
        )
        for Stream, MetaValue in zip(Container.Streams, Metadata, strict=True)
    )
    Bodies: list[DocumentBody] = []
    for PartValue in Container.Parts:
        if not PartValue.Name.startswith(
            "Breps.BlobParts/BREP."
        ) or not PartValue.Name.endswith(".smbh"):
            raise ValueError("Unsupported Fusion document part")
        Bodies.append(DocumentBody(PartValue.Name, ReadHistory(PartValue.Payload)))
    return DocumentModel(
        Container.Document,
        Container.Asset,
        Segments,
        tuple(Bodies),
        Container.Previews,
        Container.EmptyFolders,
    )
