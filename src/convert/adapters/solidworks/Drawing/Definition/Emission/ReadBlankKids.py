from collections.abc import Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedConceptNode,
)


# shared body codecs expose mutable rows while drawing ownership still requires an ordered node sequence
def ReadBlankKids(OwnerValue: ArchiveNode) -> tuple[ArchiveNode, ...]:
    FieldsValue = NeedConceptMap(OwnerValue.FieldsValue["f60"])
    ItemsValue = NeedConceptMap(FieldsValue["list"])["items"]
    if not isinstance(ItemsValue, Sequence) or isinstance(
        ItemsValue, (str, bytes, bytearray)
    ):
        raise BodyUnsupported(
            "blank drawing Definition requires ordered concept children"
        )
    return tuple(
        NeedConceptNode(NeedConceptMap(ItemValue)["o"])
        for ItemValue in CastValue(Sequence[object], ItemsValue)
    )
