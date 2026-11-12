from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Model.DraftEntity import DraftEntity
from convert.formats.Fusion.DocumentCodec.Records.DraftSubjects import DraftSubjects
from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import (
    ReadInteger,
    ReadString,
)
from convert.formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.formats.Fusion.EntityCodec.Model.NamedMetadata import NamedMetadata


def DraftFrame(Author: AuthorState, Entity: DraftEntity) -> EntityFrame:
    Subjects = DraftSubjects(Author, Entity)
    Metadata = (
        None
        if Entity.NamedPairs is None
        else tuple(
            NamedMetadata(
                ReadString(Entry["name"]),
                ReadString(Entry["metatype"]),
                ReadInteger(Entry["value"]),
            )
            for Entry in Entity.NamedPairs
        )
    )
    return EntityFrame(Entity.RootName, Subjects, Metadata)
