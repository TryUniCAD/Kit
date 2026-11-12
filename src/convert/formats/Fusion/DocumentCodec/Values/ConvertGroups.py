from convert.formats.Fusion.DocumentCodec.Values.ConvertFields import ConvertFields
from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import (
    ReadObject,
    ReadSeries,
    ReadString,
)
from convert.formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup


def ConvertGroups(
    Value: object, Catalog: dict[str, NativeSchema]
) -> tuple[EntityGroup, ...]:
    Groups: list[EntityGroup] = []
    for Entry in ReadSeries(Value):
        Fields = ReadObject(Entry)
        ClassGuid = ReadString(Fields["identifier"])
        Schema = Catalog[ClassGuid.upper()].Value
        Groups.append(
            EntityGroup(
                ClassGuid, ConvertFields(Fields["fields"], Schema.Members, Catalog)
            )
        )
    return tuple(Groups)
