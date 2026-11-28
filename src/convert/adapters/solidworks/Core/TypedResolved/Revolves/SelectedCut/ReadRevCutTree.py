from collections import Counter

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveClasses import (
    KRevolveClasses,
)


# the scoped graph needs two independent stock roots before its one ordinary revolve cut
def ReadRevCutTree(LinkValue: NativeLink) -> dict[int, ArchiveNode]:
    if any(
        not Report.get("completed")
        or Report.get("missing_schemas")
        or Report.get("provisional_schemas")
        for Report in (
            LinkValue.ConfigValue.ReportValue,
            LinkValue.ResolvedValue.ReportValue,
        )
    ):
        raise ValueError(
            "selected revolve cut requires complete linked archive grammar"
        )
    Features = IndexFeatures(LinkValue)
    Actual = tuple(Value.ClassValue.NameValue for Value in Features.values())
    Expected = dict.fromkeys(
        KRevolveClasses - {"moProfileFeature_c", "moRevolution_c"}, 1
    )
    Expected["moRefPlane_c"] = 3
    if Counter(Actual[:-6]) != Expected or Actual[-6:] != (
        "moProfileFeature_c",
        "moRevolution_c",
        "moProfileFeature_c",
        "moRevolution_c",
        "moProfileFeature_c",
        "moRevCut_c",
    ):
        raise ValueError(
            "selected revolve cut requires its three ordered profile and operation pairs"
        )
    return Features
