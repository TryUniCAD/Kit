from convert.adapters.solidworks.Archive.Construction.Nodes.InitNodeMut import (
    InitNodeMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# concepts require fresh owned child lists while preserving the preallocated native object identity
def InitConceptMut(
    NodeValue: ArchiveNode,
    NameValue: str | None,
    Allocator: PersistentIds | None = None,
) -> None:
    InitNodeMut(NodeValue, NameValue, Allocator)
    NodeValue.FieldsValue.update(
        {
            "has_list68": 0,
            "f78": None,
            "f60": {"list": {"n": 0, "items": []}, "tail": 0},
        }
    )
