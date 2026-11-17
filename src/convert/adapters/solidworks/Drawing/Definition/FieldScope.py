from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Drawing.Definition.ConceptState import ConceptState


# embedded archive fields inherit outer values while retaining their own identity
@DataClass(slots=True)
class FieldScope:
    Reader: GraphReader
    Context: ConceptState
    OwnerName: str
    Fields: MutableMapping[str, object]
    Parent: FieldScope | None = None

    # optional native fields must distinguish absent values from values stored as null
    def FindField(self, FieldName: str) -> tuple[bool, object]:
        if FieldName in self.Fields:
            return True, self.Fields[FieldName]
        if self.Parent is None:
            return False, None
        return self.Parent.FindField(FieldName)

    # an embedded owner shares the map and callback context with its caller
    def ChildScope(self) -> FieldScope:
        return FieldScope(self.Reader, self.Context, self.OwnerName, {}, self)
