from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import (
    InitFeatureMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# independently mapped generic feature fields serve each concrete mate and its anonymous datum without saved payloads
def MakeFeature(
    ClassName: str,
    NameValue: str | None,
    OwnerValue: ArchiveNode,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds | None = None,
) -> ArchiveNode:
    if ClassName not in ("moMateCoincident", "moMateParallel", "moRefPlane_c"):
        raise ValueError(
            "fresh feature requires a qualified concrete class owner and release target"
        )
    NodeValue = ArchiveNode(RuntimeClass(ClassName, 1), {})
    InitFeatureMut(NodeValue, NameValue, OwnerValue, TargetValue, Allocator)
    return NodeValue
