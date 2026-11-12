from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    SubtypeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.SubtypeFamily import (
    KSubtypeFamily,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.EntitySubtree import (
    EntitySubtree,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.ListSubtypes import (
    ListSubtypes,
)
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity


def CheckSubtypes(Entities: tuple[KJournalEntity, ...]) -> None:
    Families: list[str] = []
    for Entity in Entities:
        for Found in ListSubtypes(EntitySubtree(Entity)):
            if isinstance(Found, SubtypeNode):
                Families.append(KSubtypeFamily[Found.SubtypeName])
            elif (
                not 0 <= Found.Index < len(Families)
                or Families[Found.Index] != Found.Family
            ):
                raise ValueError(
                    "Fusion subtype reference is absent or family-incompatible"
                )
