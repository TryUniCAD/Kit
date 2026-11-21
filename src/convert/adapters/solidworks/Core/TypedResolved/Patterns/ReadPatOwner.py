from collections import Counter

from convert.adapters.solidworks.Archive.Construction.System.SystemClasses import (
    KSystemExtras,
    KSystemFolders,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Patterns.CheckPatMode import (
    CheckPatMode,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatternOwner import (
    PatternOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadPatChain import (
    ReadPatChain,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadPatDatum import (
    ReadPatDatum,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadPatDrivers import (
    ReadPatDrivers,
)


# the narrow public refinement needs exactly the ordinary feature and helper roots
def ReadPatOwner(LinkValue: NativeLink, HeaderValue: ArchiveNode) -> PatternOwner:
    Features = IndexFeatures(LinkValue)
    RootsValue = tuple(Features.values())
    Classes = tuple(Value.ClassValue.NameValue for Value in RootsValue)
    SystemCounts = dict.fromkeys(KSystemFolders | KSystemExtras, 1)
    SystemCounts["moRefPlane_c"] = 3
    if LinkValue.ConfigValue.RootValue.ClassValue.NameValue != "moPart_c" or (
        Counter(Classes[:-5]) != SystemCounts
        or Classes[-5:]
        != (
            "moProfileFeature_c",
            "moExtrusion_c",
            "moProfileFeature_c",
            "moICE_c",
            "moLPattern_c",
        )
    ):
        raise ValueError(
            "ordinary linear pattern requires its ordered plate seed and pattern roots"
        )
    SeedValue, PatternValue = RootsValue[-2:]
    CheckPatMode(PatternValue)
    AtomsValue, Output = ReadPatChain(LinkValue, RootsValue)
    return PatternOwner(
        PatternValue,
        SeedValue,
        ReadPatDatum(LinkValue, HeaderValue, Features, PatternValue),
        ReadPatDrivers(LinkValue, PatternValue),
        AtomsValue,
        Output,
    )
