from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the stored mode depends on the owning end spec and retains only the active angular dimensions
def MakeRevEnd(
    FeatureValue: ArchiveNode,
    AngleValue: DimensionGraph,
    SideMode: str = "one_sided",
    Against: DimensionGraph | None = None,
) -> ArchiveNode:
    if SideMode not in ("one_sided", "symmetric_full", "two_sided") or (
        (SideMode == "two_sided") != (Against is not None)
    ):
        raise ValueError("revolve end mode and angular displays disagree")
    return ArchiveNode(
        RuntimeClass("moRevEndSpec_c", 1),
        {
            "f08": int(SideMode == "one_sided"),
            "f138": 0,
            "f13c": 0,
            "f0c": 6 if SideMode == "symmetric_full" else 0,
            "f10": 0,
            "f118": None,
            "f120": None,
            "f128": None,
            "f130": None,
            "f38": 0.01,
            "f40": 0.01,
            "f140": 0,
            "f144": 0,
            "f18": AngleValue.DisplayValue,
            "f20": None if Against is None else Against.DisplayValue,
            "f28": None,
            "f30": None,
            "owner": FeatureValue,
        },
    )
