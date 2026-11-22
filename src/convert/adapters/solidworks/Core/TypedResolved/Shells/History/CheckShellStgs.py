from convert.adapters.solidworks.Archive.Partition.History.XmtDelta import XmtDelta
from convert.adapters.solidworks.Archive.Partition.History.XmtStage import XmtStage
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt


# a historical world must name the real live body at each controller boundary
def CheckStageWorld(
    StageValue: XmtStage, BodyIndex: int, AliveValue: bool, ActiveValue: bool
) -> None:
    WorldValue = RequireXmt(StageValue.NodesValue, 1, 101)
    BodyIds = {
        Value.IndexValue
        for Value in StageValue.NodesValue.values()
        if Value.KindValue == 12
    }
    if (
        WorldValue.Integer("body") != BodyIndex
        or BodyIds != ({BodyIndex} if BodyIndex else set())
        or WorldValue.Integer("alive") != int(AliveValue)
        or WorldValue.Integer("assembly")
        or (
            not ActiveValue
            and any(
                WorldValue.Integer(NameValue)
                for NameValue in ("current_id", "highest_id")
            )
        )
    ):
        raise ValueError("SOLIDWORKS shell rollback restores a foreign world state")


# only the shell modifies the retained body while the stock creates the actual body slot
def CheckShellStgs(StagesValue: tuple[XmtStage, ...]) -> XmtDelta:
    Current, Stock, Activation, Initial = StagesValue
    BodyIndex = RequireXmt(Current.NodesValue, 1, 101).Integer("body")
    for StageValue, IndexValue, AliveValue, ActiveValue in (
        (Current, BodyIndex, True, True),
        (Stock, BodyIndex, True, False),
        (Activation, 0, True, False),
        (Initial, 0, False, False),
    ):
        CheckStageWorld(StageValue, IndexValue, AliveValue, ActiveValue)
    Previous = RequireXmt(Stock.NodesValue, BodyIndex, 12)
    Effect, Creator, Start = Current.UndoValue, Stock.UndoValue, Activation.UndoValue
    if (
        Effect is None
        or Creator is None
        or Start is None
        or Initial.UndoValue is not None
        or not any(Value is Previous for Value in Effect.PreviousValue)
        or any(Value.KindValue == 12 for Value in Effect.RestoredValue)
        or any(KindValue == 12 for _, KindValue in Effect.RemovedValue)
        or (BodyIndex, 12) not in Creator.RemovedValue
        or Creator.RestoredValue
        or Start.RestoredValue
        or Start.RemovedValue
    ):
        raise ValueError(
            "SOLIDWORKS shell rollback does not retain the actual stock body"
        )
    return Effect
