from typing import TypedDict

from convert.formats.Fusion.EntityCodec.Vocabulary.FieldJson import FieldJson


class SchemaJson(TypedDict):
    ClassGuid: str
    BaseGuid: str
    SchemaVersion: int
    Members: list[FieldJson]
    IsValue: bool
