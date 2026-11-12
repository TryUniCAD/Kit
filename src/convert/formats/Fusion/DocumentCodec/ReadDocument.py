from collections.abc import Callable

from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Reading.ReadDocParts import ReadDocParts
from convert.formats.Fusion.DocumentCodec.Reading.Materials.CheckDocMats import (
    CheckDocMats,
)
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
    Bodies, Materials = ReadDocParts(Container.Parts)
    Result = DocumentModel(
        Container.Document,
        Container.Asset,
        Segments,
        Bodies,
        Container.Previews,
        Container.EmptyFolders,
        Materials,
    )
    CheckDocMats(Result)
    return Result
