from typing import TypedDict

from tests.convert.formats.FusionCodec.Entities.WireJson import WireJson


class FieldJson(TypedDict):
    FieldName: str
    ValueType: WireJson
    IsSaved: bool
