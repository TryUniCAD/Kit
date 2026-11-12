from typing import TypedDict

from tests.convert.formats.FusionCodec.Entities.FieldJson import FieldJson


class ClassJson(TypedDict):
    ClassGuid: str
    BaseGuid: str
    SchemaVersion: int
    Members: list[FieldJson]
    IsValue: bool
