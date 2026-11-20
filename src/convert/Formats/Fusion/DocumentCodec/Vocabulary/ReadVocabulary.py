from functools import lru_cache as CacheValues
from json import loads as LoadJson
from pathlib import Path
from typing import cast as CastValue

from convert.Formats.Fusion.DocumentCodec.Values.ReadObjects import (
    IsTrueValue,
    ReadInteger,
    ReadObject,
    ReadSeries,
    ReadString,
)
from convert.Formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.Formats.Fusion.DocumentCodec.Vocabulary.ReadWireType import ReadFieldSpec
from convert.Formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema


# vocabulary contents keep decoding current when a research checkout changes between reads
def ReadVocabulary(Source: Path) -> tuple[NativeSchema, ...]:
    SourceText = Source.read_text(encoding="utf-8")
    if len(SourceText) > 512 * 1024:
        return ParseVocab(SourceText)
    return CachedVocab(SourceText)


# bounded immutable vocabulary entries let readers reuse the same validated class definitions
@CacheValues(maxsize=16)
def CachedVocab(SourceText: str) -> tuple[NativeSchema, ...]:
    return ParseVocab(SourceText)


# a shared parser keeps cached and oversized vocabulary inputs on the same validation path
def ParseVocab(SourceText: str) -> tuple[NativeSchema, ...]:
    Values = ReadSeries(CastValue(object, LoadJson(SourceText)))
    Result: list[NativeSchema] = []
    for Value in Values:
        Fields = ReadObject(Value)
        Schema = ClassSchema(
            ReadString(Fields["ClassGuid"]),
            ReadString(Fields["BaseGuid"]),
            ReadInteger(Fields["SchemaVersion"]),
            tuple(ReadFieldSpec(Entry) for Entry in ReadSeries(Fields["Members"])),
            IsTrueValue(Fields["IsValue"]),
        )
        Result.append(
            NativeSchema(
                ReadString(Fields["NameValue"]),
                ReadString(Fields["ClassSpace"]),
                Schema,
            )
        )
    return tuple(Result)
