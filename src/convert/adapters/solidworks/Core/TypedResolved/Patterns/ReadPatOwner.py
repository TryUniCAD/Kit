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
    Features = IndexFeatures(LinkValue, PartPattern=True)
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
    if Classes[-7:] != (*StockKinds, "moRefAxis_c", "moRefPlane_c", "moLPattern_c"):
        raise ValueError(
            "cold linear pattern requires actual plate, seed and oblique datum roots"
        )
    if (
        LinkValue.ConfigValue.RootValue.ClassValue.NameValue != "moPart_c"
        or Counter(Classes[:-7]) != SystemCounts
    ):
        raise ValueError("cold linear pattern requires the ordinary part tree")
    StockValue = RootsValue[-7:-3]
    SeedValue, PatternValue = StockValue[-1], RootsValue[-1]
    CheckPatMode(PatternValue)
    AtomsValue, Output = ReadPatChain(LinkValue, (*StockValue, PatternValue))
    return PatternOwner(
        PatternValue,
        SeedValue,
        ReadPatDatum(LinkValue, HeaderValue, Features, PatternValue, RootsValue[-3]),
        ReadPatDrivers(LinkValue, PatternValue),
        AtomsValue,
        Output,
    )
