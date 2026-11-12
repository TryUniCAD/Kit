from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.ContainerCodec.Model.AssetHeader import AssetHeader
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.ContainerCodec.Model.DocumentHeader import DocumentHeader
from convert.formats.Fusion.ContainerCodec.Model.SegmentStreams import SegmentStreams


@MakeDataClass(frozen=True, slots=True)
class FusionContainer:
    Document: DocumentHeader
    Asset: AssetHeader
    Streams: tuple[SegmentStreams, ...]
    Previews: tuple[ContainerPart, ...]
    Parts: tuple[ContainerPart, ...] = ()
    EmptyFolders: tuple[str, ...] = ()
