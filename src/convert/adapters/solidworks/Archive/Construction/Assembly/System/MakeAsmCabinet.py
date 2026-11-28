from convert.adapters.solidworks.Archive.Construction.Assembly.System.MakeAsmNode import (
    MakeAsmNode,
)
from convert.adapters.solidworks.Archive.Construction.Model.EmptyRootRows import (
    EmptyRootRows,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# native annotation cabinet construction retains distinct empty annotation arrays and the documented initial unit scaling
def MakeAsmCabinet(
    NameValue: str,
    OwnerValue: ArchiveNode,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> ArchiveNode:
    NodeValue = MakeAsmNode(
        "moDetailCabinet_c", NameValue, OwnerValue, TargetValue, Allocator
    )
    NodeValue.FieldsValue.update(
        {
            "f368": EmptyRootRows(),
            "f370": 1.0,
            "f378": 1.0,
            "f388": EmptyRootRows(),
            "n3d8": 0,
            "f3d8": [],
            "f3f0": 0,
        }
    )
    return NodeValue
