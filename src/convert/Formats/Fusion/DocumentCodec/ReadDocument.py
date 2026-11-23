from collections.abc import Callable
from itertools import chain as ChainValues

from convert.Formats.Fusion.ContainerCodec.ReadIndexed import ReadIndexed
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Configuration.CheckDocConfig import (
    CheckDocConfig,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Images.CheckDocImages import (
    CheckDocImages,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Links.CheckDocLinks import (
    CheckDocLinks,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Form.CheckDocForms import (
    CheckDocForms,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Mesh.CheckDocMeshes import (
    CheckDocMeshes,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Graphics.CheckDocScene import (
    CheckDocScene,
)
from convert.Formats.Fusion.DocumentCodec.Reading.ReadDocParts import ReadDocParts
from convert.Formats.Fusion.DocumentCodec.Reading.Materials.CheckDocMats import (
    CheckDocMats,
)
from convert.Formats.Fusion.DocumentCodec.Records.DecodeSegment import DecodeSegment
from convert.Formats.Fusion.DocumentCodec.Records.MakeSegProfile import MakeSegProfile
from convert.Formats.Fusion.DocumentCodec.Records.MakeTargets import MakeTargets
from convert.Formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas


# the document operation needs a distinct decoding boundary so model state retains its native feature and ownership relationships
def ReadDocument(
    Payload: bytes, InflateZstd: Callable[[bytes, int], bytes] | None = None
) -> DocumentModel:
    Container, Indexes = ReadIndexed(Payload, InflateZstd)
    Schemas = ReadDocSchemas()
    TargetRows = tuple(MakeTargets(IndexValue.Metadata) for IndexValue in Indexes)
    Segments = tuple(
        DecodeSegment(
            Stream.BulkData,
            IndexValue,
            MakeSegProfile(
                Schemas,
                IndexValue.Metadata,
                tuple(
                    ChainValues.from_iterable(
                        TargetRows[:Order] + TargetRows[Order + 1 :]
                    )
                ),
            ),
        )
        for Order, (Stream, IndexValue) in enumerate(
            zip(Container.Streams, Indexes, strict=True)
        )
    )
    del Indexes
    Parts = ReadDocParts(Container.Parts)
    Result = DocumentModel(
        Container.Document,
        Container.Asset,
        Segments,
        Parts.Bodies,
        Container.Previews,
        Container.EmptyFolders,
        Parts.Materials,
        Parts.Snapshots,
        Parts.Configurations,
        Parts.Graphics,
        Parts.Meshes,
        Parts.Forms,
        Container.Properties,
        Container.Redirects,
        Parts.Images,
    )
    CheckDocMats(Result)
    CheckDocConfig(Result)
    CheckDocLinks(Result)
    CheckDocScene(Result)
    CheckDocMeshes(Result)
    CheckDocForms(Result, False)
    CheckDocImages(Result)
    return Result
