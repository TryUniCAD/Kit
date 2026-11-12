from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class NumberBinding:
    OwnerId: int
    ParamId: int
    BookId: int
    SlotIndex: int
    BoundRank: int
    Number: float
