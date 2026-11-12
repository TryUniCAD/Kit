from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.ContainerCodec.Model.AssetHeader import AssetHeader
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.ContainerCodec.Model.DocumentHeader import DocumentHeader
from convert.formats.Fusion.DocumentCodec.Model.DocumentBody import DocumentBody
from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment


@MakeDataClass(frozen=True, slots=True)
class DocumentModel:
    Document: DocumentHeader
    Asset: AssetHeader
    Segments: tuple[ParsedSegment, ...]
    Bodies: tuple[DocumentBody, ...]
    Previews: tuple[ContainerPart, ...]
    EmptyFolders: tuple[str, ...]
