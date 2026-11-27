from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Model.InitModelMut import (
    InitModelMut,
)
from convert.adapters.solidworks.Archive.Construction.Model.MakePartSeeds import (
    MakePartSeeds,
)
from convert.adapters.solidworks.Archive.Construction.Model.PartRootInput import (
    PartRootInput,
)
from convert.adapters.solidworks.Archive.Construction.Model.PartRootRefs import (
    PartRootRefs,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootRefs import (
    RequireRootRefs,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitConceptMut import (
    InitConceptMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the concrete part root must be fresh and completely constructed before configuration and feature attachment begins
def MakePartRootMut(
    InputValue: PartRootInput, RefsValue: PartRootRefs, Allocator: PersistentIds
) -> ArchiveNode:
    if type(CastValue(object, InputValue)) is not PartRootInput:
        raise TypeError("part root construction requires validated explicit inputs")
    if not isinstance(CastValue(object, Allocator), PersistentIds):
        raise TypeError(
            "part root construction requires its actual persistent allocator"
        )
    RequireRootRefs(RefsValue)
    NodeValue = ArchiveNode(RuntimeClass("moPart_c", 1), {})
    InitConceptMut(NodeValue, InputValue.NameValue, Allocator)
    InitModelMut(NodeValue, RefsValue)
    NodeValue.FieldsValue.update(MakePartSeeds(InputValue.HatchName))
    return NodeValue
