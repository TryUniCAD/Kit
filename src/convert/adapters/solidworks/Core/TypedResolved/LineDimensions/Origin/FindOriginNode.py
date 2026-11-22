from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId


# a selected feature number must resolve to exactly one real origin in this same linked part archive
def FindOriginNode(LinkValue: NativeLink, FeatureId: object) -> ArchiveNode:
    if (
        type(FeatureId) is not int
        or FeatureId < 0
        or LinkValue.ConfigValue.RootValue.ClassValue.NameValue != "moPart_c"
    ):
        raise ValueError("typed origin reference has no actual ordinary part owner")
    NodesValue = tuple(
        NodeValue
        for NodeValue in LinkValue.ResolvedValue.RootsValue
        if NodeValue is not None
        and NodeValue.ClassValue.NameValue == "moOriginProfileFeature_c"
        and NativeNodeId(NodeValue) == FeatureId
    )
    if len(NodesValue) != 1:
        raise ValueError("typed origin reference has a missing or ambiguous target")
    return NodesValue[0]
