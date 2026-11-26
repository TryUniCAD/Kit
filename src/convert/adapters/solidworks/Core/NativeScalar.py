from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Core.NativeOperand import NativeOperand


# feature readers bind scalar values to their original byte offsets
@Dataclass(frozen=True, slots=True)
class NativeScalar:
    name: str
    name_offset: int
    value_offset: int
    value: float
    object_id: int | None
    role: str
    operands: tuple[NativeOperand, ...]
