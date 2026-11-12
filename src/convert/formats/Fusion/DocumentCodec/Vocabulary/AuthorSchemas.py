from pathlib import Path

from convert.formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.formats.Fusion.DocumentCodec.Vocabulary.ReadVocabulary import (
    ReadVocabulary,
)


def AuthorSchemas(ProfileKind: str) -> tuple[NativeSchema, ...]:
    Source = Path(__file__).parent
    Schemas = ReadVocabulary(Source / "DesignClasses.json")
    if ProfileKind not in ("rectangle", "cuboid"):
        return Schemas
    Selected = {Schema.Value.ClassGuid.upper(): Schema for Schema in Schemas}
    for Schema in ReadVocabulary(Source / "RectangleClasses.json"):
        Selected[Schema.Value.ClassGuid.upper()] = Schema
    return tuple(Selected.values())
