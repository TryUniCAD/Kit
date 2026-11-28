from dataclasses import dataclass as Dataclass


# constraint records must retain operands independently of adapter construction
@Dataclass(frozen=True, slots=True)
class NativeRule:
    id: str
    kind: str
    references: tuple[str, ...]
    parameter: str | None
    value: float | None
    native_offset: int | None
    native_code: int | None
    reference_points: tuple[str, ...] = ()
    native_length: int = 8
