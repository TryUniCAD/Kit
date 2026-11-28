from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptNode,
)


# drawing view order belongs to the resolved native concept node list
def ReadOwnedNodes(Owner: ArchiveNode) -> tuple[ArchiveNode, ...]:
    ConceptList = NeedConceptMap(Owner.FieldsValue.get("f60"))
    Items = NeedConceptMap(ConceptList.get("list")).get("items")
    if not isinstance(Items, tuple):
        raise ValueError("SOLIDWORKS drawing concept has an invalid native node list")
    return tuple(
        NeedConceptNode(NeedConceptMap(ItemValue).get("o"))
        for ItemValue in CastValue(tuple[object, ...], Items)
    )
