from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# each ordinary occurrence configuration owns a fresh one target reference path with no independent configuration or retained runtime lifetime count
def MakeRefChain(TargetValue: ArchiveNode) -> ArchiveNode:
    TargetsValue = ArchiveNode(
        RuntimeClass("moExtFeatureList_c", 1), {"n": 1, "f08": [{"o": TargetValue}]}
    )
    return ArchiveNode(
        RuntimeClass("moReferenceChain_c", 1),
        {"f08": TargetsValue, "f20": 0, "f24": 0, "f40": {"f08": "", "f10": -1}},
    )
