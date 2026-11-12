from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class PatchCell:
    Face: int
    Window: tuple[int, int, int, int]
    Offset: tuple[int, int, int]
