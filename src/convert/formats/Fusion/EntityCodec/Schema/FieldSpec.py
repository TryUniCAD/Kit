from __future__ import annotations

from dataclasses import dataclass as MakeDataClass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType


@MakeDataClass(frozen=True, slots=True)
class FieldSpec:
    FieldName: str
    ValueType: WireType
    IsSaved: bool = True
