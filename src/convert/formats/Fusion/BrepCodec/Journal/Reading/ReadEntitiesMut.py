from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntityNode import (
    ReadEntityNode,
)
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmName, ReadAsmRecord


def ReadEntitiesMut(Cursor: MetaCursor, EndName: str) -> tuple[KJournalEntity, ...]:
    Entities: list[KJournalEntity] = []
    while (NameValue := ReadAsmName(Cursor)) != EndName:
        if len(Entities) >= 1024:
            raise ValueError("Oversized Fusion journal entity table")
        Entities.append(ReadEntityNode(ReadAsmRecord(Cursor, NameValue)))
    return tuple(Entities)
