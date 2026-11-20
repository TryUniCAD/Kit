from dataclasses import dataclass as Dataclass


# native dimension operands retain their serialized entity and kind indices
@Dataclass(frozen=True, slots=True)
class NativeOperand:
    offset: int
    kind_code: int
    entity_index: int
