from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger


@MakeDataClass(frozen=True, slots=True)
class HistoryState:
    CurrentId: int
    InitialId: int
    Generation: int
    Allocation: int
    BoardNumber: int

    def __post_init__(self) -> None:
        Values = (
            self.CurrentId,
            self.InitialId,
            self.Generation,
            self.Allocation,
            self.BoardNumber,
        )
        for Value in Values:
            CheckInteger(Value, "history metadata", Lower=0)
        if self.CurrentId <= self.InitialId:
            raise ValueError(
                "Fusion BRep current history state must follow its initial state"
            )
