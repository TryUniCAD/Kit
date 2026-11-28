from collections.abc import Mapping
from dataclasses import dataclass as Dataclass, field as Field

from convert.adapters.solidworks.Core.NativeOperand import NativeOperand


# dimension display text and binary measurements must retain separate provenance
@Dataclass(frozen=True, slots=True)
class NativeDimension:
    name: str
    value_mm: float | None
    kind: str
    source_text: str
    native_value: float | None = None
    native_offset: int | None = None
    native_role: str | None = None
    operands: tuple[NativeOperand, ...] = ()
    inch_display_value: float | None = None
    native_stream: str | None = None
    TypedOwner: Mapping[str, object] = Field(default_factory=dict[str, object])
