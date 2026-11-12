from typing import TypedDict

from tests.convert.formats.FusionCodec.Entities.ClassJson import ClassJson
from tests.convert.formats.FusionCodec.Entities.WireJson import WireJson


class NamedSchema(TypedDict):
    TypeName: str
    ValueType: WireJson


class ArchiveSchema(TypedDict):
    Classes: list[str]
    MetadataHash: str


class CorpusSchema(TypedDict):
    RootGuid: str
    Classes: dict[str, ClassJson]
    Profiles: dict[str, ArchiveSchema]
    NamedTypes: list[NamedSchema]
