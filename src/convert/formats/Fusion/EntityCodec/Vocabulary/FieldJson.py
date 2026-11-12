from typing import TypedDict

from convert.formats.Fusion.EntityCodec.Vocabulary.WireJson import WireJson


class FieldJson(TypedDict):
    FieldName: str
    ValueType: WireJson
    IsSaved: bool
