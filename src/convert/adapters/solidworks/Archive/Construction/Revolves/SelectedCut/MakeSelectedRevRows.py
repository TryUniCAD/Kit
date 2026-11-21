from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import (
    KeywordFeature,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Part.MakeRevKeyRows import (
    MakeRevKeyRows,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Part.MakeRevKeys import (
    MakeRevSystemRows,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the measured selected cut keyword index lists three driving features before their consumed sketches
def MakeSelectedRevRows(
    SystemNodes: tuple[ArchiveNode, ...],
    Profiles: tuple[ArchiveNode, ...],
    Features: tuple[ArchiveNode, ...],
    Operations: tuple[RevolvePlan, ...],
) -> tuple[KeywordFeature, ...]:
    KeyPairs = tuple(
        MakeRevKeyRows(Profile, Feature, Operation)
        for Profile, Feature, Operation in zip(
            Profiles, Features, Operations, strict=True
        )
    )
    FeaturesRows = tuple(Row for _, Row in KeyPairs)
    return (
        *MakeRevSystemRows(SystemNodes),
        *FeaturesRows[:-1],
        ReplaceValue(FeaturesRows[-1], KindValue="Cut-Revolve"),
        *(Row for Row, _ in KeyPairs),
    )
