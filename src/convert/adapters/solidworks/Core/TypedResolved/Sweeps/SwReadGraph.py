from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwProfile import (
    SwReadProfile,
)


# the saved and cold projections consume the same typed feature and profile owners
@DataClass(frozen=True, slots=True)
class SwReadGraph:
    LinkValue: NativeLink
    FeatureValue: ArchiveNode
    SectionValue: SwReadProfile
    PathValue: SwReadProfile
    DatumValues: tuple[ArchiveNode, ...]
    ConfigValue: ArchiveNode
    DensityValue: ArchiveNode
