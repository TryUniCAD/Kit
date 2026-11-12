from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.Model.ConfigPart import ConfigPart
from convert.formats.Fusion.DocumentCodec.Model.DocumentBody import DocumentBody
from convert.formats.Fusion.DocumentCodec.Model.DocumentSnap import DocumentSnap
from convert.formats.Fusion.DocumentCodec.Model.MaterialPart import MaterialPart


@MakeDataClass(frozen=True, slots=True)
class DocumentParts:
    Bodies: tuple[DocumentBody, ...]
    Materials: tuple[MaterialPart, ...]
    Snapshots: tuple[DocumentSnap, ...]
    Configurations: tuple[ConfigPart, ...]
