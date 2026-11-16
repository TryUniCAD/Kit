from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass as DataClass
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# native object references depend on identity even when field payloads are equal
@DataClass(eq=False, slots=True)
class ArchiveNode:
    ClassValue: RuntimeClass | ExternalClass
    FieldsValue: MutableMapping[str, object]
    StartOffset: int | None = None
    EndOffset: int | None = None
    IndexValue: int | None = None

    # graph payload ownership must be valid before recursive body decoding begins
    def __post_init__(self) -> None:
        if type(self.ClassValue) not in (RuntimeClass, ExternalClass):
            raise TypeError("archive node class must be a typed descriptor")
        if not isinstance(CastValue(object, self.FieldsValue), MutableMapping):
            raise TypeError("archive node fields must be a mutable mapping")
        if any(type(FieldName) is not str for FieldName in self.FieldsValue):
            raise TypeError("archive node field names must be strings")

    # compatibility factories may extend nodes while malformed callback results must fail
    @staticmethod
    def RequireNode(NodeValue: object) -> ArchiveNode:
        if not isinstance(NodeValue, ArchiveNode):
            raise TypeError("archive object must be an archive node")
        return NodeValue
