from json import loads as LoadJson
from pathlib import Path
from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import ReadObject


def FeatureDefaults() -> dict[str, dict[str, object]]:
    Source = Path(__file__).parent / "FeatureDefaults.json"
    Values = ReadObject(CastValue(object, LoadJson(Source.read_text(encoding="utf-8"))))
    return {NameValue: dict(ReadObject(Fields)) for NameValue, Fields in Values.items()}
