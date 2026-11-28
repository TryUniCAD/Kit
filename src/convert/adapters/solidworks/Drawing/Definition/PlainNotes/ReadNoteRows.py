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
    if not isinstance(Items, Sequence) or isinstance(Items, (str, bytes, bytearray)):
        raise BodyUnsupported("invalid drawing note collection")
    NoteItems = CastValue(Sequence[object], Items)
    CountValue = Fields.get("n")
    if type(CountValue) is not int or CountValue != len(NoteItems):
        raise BodyUnsupported("invalid drawing note collection")
    return tuple(
        NeedConceptNode(NeedConceptMap(RowValue).get("o")) for RowValue in NoteItems
    )


# single note owners must resolve to the declared class in the actual collection
def NeedOneNoteRow(Parent: ArchiveNode, FieldName: str, ClassName: str) -> ArchiveNode:
    RowValues = ReadNoteRows(NeedConceptMap(Parent.FieldsValue.get(FieldName)))
    if len(RowValues) != 1:
        raise BodyUnsupported("plain drawing note requires one owned item")
    return NeedConceptNode(RowValues[0], ClassName)
