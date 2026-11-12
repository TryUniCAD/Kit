from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Materialize import Materialize
from convert.formats.Fusion.BrepCodec.Journal.Permutation.RemapBoards import RemapBoards
from convert.formats.Fusion.BrepCodec.Journal.Permutation.RemapEntity import RemapEntity


def PermuteJournal(Model: JournalModel, Order: tuple[int, ...]) -> JournalModel:
    _ = Materialize(Model)
    if type(Order) is not tuple or any(type(Value) is not int for Value in Order):
        raise ValueError(
            "Fusion entity permutation requires immutable integer ordinals"
        )
    if len(Order) != len(Model.Entities) or sorted(Order) != list(range(len(Order))):
        raise ValueError("Fusion entity allocation is not a complete permutation")
    if Order[0] != 0 or set(Order[: Model.ActiveCount]) != set(
        range(Model.ActiveCount)
    ):
        raise ValueError(
            "Fusion allocation must preserve the header and revision partitions"
        )
    Mapping = tuple(Order.index(Index) for Index in range(len(Order)))
    Entities = tuple(RemapEntity(Model.Entities[Index], Mapping) for Index in Order)
    States = tuple(
        ReplaceValue(State, Boards=RemapBoards(State.Boards, Mapping))
        for State in Model.States
    )
    Result = ReplaceValue(Model, Entities=Entities, States=States)
    _ = Materialize(Result)
    return Result
