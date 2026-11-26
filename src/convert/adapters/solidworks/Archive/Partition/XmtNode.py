from collections.abc import Mapping
from dataclasses import dataclass as DataClass
from typing import cast as CastValue


# body ownership requires typed native indices and source fields with explicit access checks
@DataClass(frozen=True, slots=True)
class XmtNode:
    IndexValue: int
    KindValue: int
    FieldsValue: Mapping[str, object]

    # scalar identities must never accept booleans or floating point approximations
    def Integer(self, NameValue: str) -> int:
        FieldValue = self.FieldsValue[NameValue]
        if type(FieldValue) is not int:
            raise ValueError("kernel field is not an integer")
        return FieldValue

    # linked inventories need actual native index arrays before following ownership
    def Indexes(self, NameValue: str) -> tuple[int, ...]:
        FieldValue = self.FieldsValue[NameValue]
        if not isinstance(FieldValue, tuple):
            raise ValueError("kernel field is not an integer array")
        MembersValue = CastValue(tuple[object, ...], FieldValue)
        if any(type(MemberValue) is not int for MemberValue in MembersValue):
            raise ValueError("kernel field is not an integer array")
        return CastValue(tuple[int, ...], FieldValue)

    # authored labels and fixed character enums require decoded source text
    def String(self, NameValue: str) -> str:
        FieldValue = self.FieldsValue[NameValue]
        if not isinstance(FieldValue, str):
            raise ValueError("kernel field is not text")
        return FieldValue
