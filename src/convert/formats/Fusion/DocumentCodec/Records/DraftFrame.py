from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Model.DraftEntity import DraftEntity
from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import (
    ReadInteger,
    ReadString,
)
from convert.formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.formats.Fusion.EntityCodec.Model.NamedMetadata import NamedMetadata
from convert.formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def DraftFrame(Author: AuthorState, Entity: DraftEntity) -> EntityFrame:
    ObserverIndex = 1 if Entity.RoleName == "taper_binding" else 0
    Subjects = (
        tuple(
            SubjectValue(LocalRef(Author.Roles[RoleName]), ObserverIndex)
            for RoleName in Entity.Subjects
        )
        if Entity.Subjects
        else None
    )
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
