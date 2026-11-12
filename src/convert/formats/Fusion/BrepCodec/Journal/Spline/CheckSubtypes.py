from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Spline.ListSubtypes import ListSubtypes


def CheckSubtypes(Entities: tuple[KJournalEntity, ...]) -> None:
    Table: list[str] = []
    for Value in Entities:
        for KindName, Index in ListSubtypes(Value):
            if Index is None:
                Table.append(KindName)
            elif not Index < len(Table) or Table[Index] != KindName:
                raise ValueError(
                    "Fusion subtype reference precedes or mismatches its definition"
                )
