from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the single modern blind angular end must retain its actual active display and native inactive offset defaults
def MakeRevEnd(FeatureValue: ArchiveNode, AngleValue: DimensionGraph) -> ArchiveNode:
    return ArchiveNode(
        RuntimeClass("moRevEndSpec_c", 1),
        {
            "f08": 1,
            "f138": 0,
            "f13c": 0,
            "f0c": 0,
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
            "f20": None,
            "f28": None,
            "f30": None,
            "owner": FeatureValue,
        },
    )
