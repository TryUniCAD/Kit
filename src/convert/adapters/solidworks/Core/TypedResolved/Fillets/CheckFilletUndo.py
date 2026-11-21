from convert.adapters.solidworks.Archive.Partition.History.XmtStage import XmtStage
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# a true fillet undo restores the prior body name and retains the actual body transmit slot
def CheckFilletUndo(
    StagesValue: tuple[XmtStage, ...],
    LiveBody: XmtNode,
    StockBody: XmtNode,
    LiveName: XmtNode,
    StockName: XmtNode,
) -> None:
    Selected, Stock, Activation, Initial = StagesValue
    EffectUndo, StockUndo, ActivateUndo = (
        Selected.UndoValue,
        Stock.UndoValue,
        Activation.UndoValue,
    )
    if (
        EffectUndo is None
        or StockUndo is None
        or ActivateUndo is None
        or Initial.UndoValue is not None
    ):
        raise ValueError("SOLIDWORKS fillet history is missing an actual undo stage")
    if (
        LiveBody.IndexValue != StockBody.IndexValue
        or not any(NodeValue is StockBody for NodeValue in EffectUndo.PreviousValue)
        or any(NodeValue.KindValue == 12 for NodeValue in EffectUndo.RestoredValue)
        or any(KindValue == 12 for _, KindValue in EffectUndo.RemovedValue)
        or not EffectUndo.RestoredValue
        or EffectUndo.RestoredValue[0] is not StockName
        or (LiveName.IndexValue, 98) not in EffectUndo.RemovedValue
        or {
            (IndexValue, KindValue)
            for IndexValue, KindValue in StockUndo.RemovedValue
            if KindValue == 12
        }
        != {(StockBody.IndexValue, 12)}
        or StockUndo.RestoredValue
        or ActivateUndo.RestoredValue
        or ActivateUndo.RemovedValue
        or len(StockUndo.PreviousValue) != 1
        or len(ActivateUndo.PreviousValue) != 1
        or StockUndo.CopyCapacity != 1
        or ActivateUndo.CopyCapacity != 1
    ):
        raise ValueError(
            "SOLIDWORKS fillet undo does not restore its actual body and name"
        )
    Owners = (LiveBody.IndexValue, StockBody.IndexValue, 0, 0)
    for OffsetValue, (StageValue, BodyIndex) in enumerate(
        zip(StagesValue, Owners, strict=True)
    ):
        WorldValue = RequireXmt(StageValue.NodesValue, 1, 101)
        BodySlots = {
            NodeValue.IndexValue
            for NodeValue in StageValue.NodesValue.values()
            if NodeValue.KindValue == 12
        }
        if (
            WorldValue.Integer("body") != BodyIndex
            or BodySlots != ({BodyIndex} if BodyIndex else set())
            or WorldValue.Integer("alive") != int(OffsetValue < 3)
            or OffsetValue
            and any(
                WorldValue.Integer(NameValue)
                for NameValue in ("attrib_def", "current_id", "highest_id")
            )
        ):
            raise ValueError("SOLIDWORKS fillet rollback has a foreign world state")
