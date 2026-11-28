from collections import Counter

from convert.adapters.solidworks.Archive.Construction.System.SystemClasses import (
    KSystemExtras,
    KSystemFolders,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# an alternate feature history can introduce body owners outside the three recorded operations
def ReadStockRoots(LinkValue: NativeLink) -> dict[int, ArchiveNode]:
    if any(
        not ReportValue.get("completed")
        or ReportValue.get("missing_schemas")
        or ReportValue.get("provisional_schemas")
        for ReportValue in (
            LinkValue.ConfigValue.ReportValue,
            LinkValue.ResolvedValue.ReportValue,
        )
    ):
        raise ValueError("two stock lineage requires complete linked archive grammar")
    Features = IndexFeatures(LinkValue)
    ClassOrder = tuple(NodeValue.ClassValue.NameValue for NodeValue in Features.values())
    SystemCounts = dict.fromkeys(KSystemFolders | KSystemExtras, 1)
    SystemCounts["moRefPlane_c"] = 3
    ExpectedOrder = (
        "moProfileFeature_c", "moExtrusion_c", "moProfileFeature_c",
        "moICE_c", "moProfileFeature_c", "moICE_c",
    )
    if Counter(ClassOrder[:-6]) != SystemCounts or ClassOrder[-6:] != ExpectedOrder:
        raise ValueError("two stock lineage requires its independent ordered feature roots")
    return Features
