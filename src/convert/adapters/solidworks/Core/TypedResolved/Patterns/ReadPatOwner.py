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
    StockKinds = (
        "moProfileFeature_c",
        "moExtrusion_c",
        "moProfileFeature_c",
        "moICE_c",
    )
    if Classes[-7:] == (*StockKinds, "moRefAxis_c", "moRefPlane_c", "moLPattern_c"):
        StartIndex = len(Classes) - 7
        HingeValue = RootsValue[-3]
    elif Classes[-5:] == (*StockKinds, "moLPattern_c"):
        StartIndex = len(Classes) - 5
        HingeValue = None
    else:
        raise ValueError(
            "ordinary linear pattern requires ordered plate and seed roots"
        )
    if (
        LinkValue.ConfigValue.RootValue.ClassValue.NameValue != "moPart_c"
        or Counter(Classes[:StartIndex]) != SystemCounts
    ):
        raise ValueError(
            "ordinary linear pattern requires its ordered plate seed and pattern roots"
        )
    StockValue = RootsValue[StartIndex : StartIndex + 4]
    SeedValue, PatternValue = StockValue[-1], RootsValue[-1]
    CheckPatMode(PatternValue)
    AtomsValue, Output = ReadPatChain(LinkValue, (*StockValue, PatternValue))
    return PatternOwner(
        PatternValue,
        SeedValue,
        ReadPatDatum(LinkValue, HeaderValue, Features, PatternValue, HingeValue),
        ReadPatDrivers(LinkValue, PatternValue),
        AtomsValue,
        Output,
    )
