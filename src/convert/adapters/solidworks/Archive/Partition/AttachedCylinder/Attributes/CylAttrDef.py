from dataclasses import dataclass as DataClass


# each attached attribute declares its legal kernel owners and typed value slots
@DataClass(frozen=True, slots=True)
class CylAttrDef:
    OwnerSlots: tuple[int, ...]
    FieldKinds: tuple[int, ...]
    ActionsValue: tuple[int, ...]
