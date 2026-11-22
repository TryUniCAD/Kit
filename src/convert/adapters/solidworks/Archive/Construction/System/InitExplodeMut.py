from convert.adapters.solidworks.Archive.Construction.Model.EmptyRootRows import (
    EmptyRootRows,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import (
    InitFeatureMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.System.ClearSystemMut import (
    ClearSystemMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# empty exploded managers share the native feature base and placement defaults across concrete owners
def InitExplodeMut(
    NodeValue: ArchiveNode,
    OwnerValue: ArchiveNode,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> None:
    InitFeatureMut(NodeValue, None, OwnerValue, TargetValue)
    _ = Allocator.AllocateMut(NodeValue)
    NodeValue.FieldsValue.update(
        {
            "f358": None,
            "f360": None,
            "f398": 0.0,
            "f3a0": -1,
            "f3a4": -1,
            "f368": EmptyRootRows(),
        }
    )
    ClearSystemMut(NodeValue)
