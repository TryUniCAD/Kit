from convert.adapters.solidworks.Archive.Construction.Model.EmptyRootRows import (
    EmptyRootRows,
)
from convert.adapters.solidworks.Archive.Construction.Model.InitModelMut import (
    InitModelMut,
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
from convert.adapters.solidworks.Archive.Construction.System.ClearSystemMut import (
    ClearSystemMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# fresh assembly roots reuse the actual shared model initializer and add only independently classified assembly constructor state
def MakeAsmRoot(
    NameValue: str, RefsValue: PartRootRefs, Allocator: PersistentIds
) -> ArchiveNode:
    RequireRootRefs(RefsValue)
    NodeValue = ArchiveNode(RuntimeClass("moAssembly_c", 1), {})
    InitConceptMut(NodeValue, NameValue, Allocator)
    InitModelMut(NodeValue, RefsValue)
    FieldsValue = NodeValue.FieldsValue
    FieldsValue.update(
        {
            FieldName: EmptyRootRows()
            for FieldName in ("f14a0", "f14d8", "f18c8", "f18e8")
        }
    )
    FieldsValue.update(
        dict.fromkeys(
            (
                "f15a0",
                "f1608",
                "f1748",
                "f1740",
                "f1590",
                "f1868",
                "f9c0",
                "f9d8",
                "fa48",
                "fa50",
            ),
            None,
        )
    )
    FieldsValue.update(
        dict.fromkeys(
            (
                "f1560",
                "f1570",
                "f1750",
                "f1598",
                "f1710",
                "f1940",
                "has_f1a18",
                "has_f1a20",
            ),
            0,
        )
    )
    FieldsValue.update({"f1a28": 1, "f1674": -1})
    ClearSystemMut(NodeValue)
    return NodeValue
