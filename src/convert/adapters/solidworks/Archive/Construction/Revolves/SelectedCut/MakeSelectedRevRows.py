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
    MakeSysRevRows,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the measured selected cut keyword index lists three driving features before their consumed sketches
def MakeSelRevRows(
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
    FeaturesRows = tuple(KeyRow for _, KeyRow in KeyPairs)
    return (
        *MakeSysRevRows(SystemNodes),
        *FeaturesRows[:-1],
        ReplaceValue(FeaturesRows[-1], KindValue="Cut-Revolve"),
        *(KeyRow for KeyRow, _ in KeyPairs),
    )
