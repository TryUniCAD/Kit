from collections.abc import Mapping, Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedConceptNode,
)


# a note collection needs its actual declared count and ordered concrete object pointers
def ReadNoteRows(Fields: Mapping[str, object]) -> tuple[ArchiveNode, ...]:
    Items = Fields.get("items")
    if (
        not isinstance(Items, Sequence)
        or isinstance(Items, (str, bytes, bytearray))
        or type(Fields.get("n")) is not int
        or Fields.get("n") != len(Items)
    ):
        raise BodyUnsupported("invalid drawing note collection")
    return tuple(
        NeedConceptNode(NeedConceptMap(Row).get("o"))
        for Row in CastValue(Sequence[object], Items)
    )


# single note owners must resolve to the declared class in the actual collection
def NeedOneNoteRow(Parent: ArchiveNode, FieldName: str, ClassName: str) -> ArchiveNode:
    Rows = ReadNoteRows(NeedConceptMap(Parent.FieldsValue.get(FieldName)))
    if len(Rows) != 1:
        raise BodyUnsupported("plain drawing note requires one owned item")
    return NeedConceptNode(Rows[0], ClassName)
