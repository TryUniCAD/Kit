from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.History.ApplyXmtUndo import (
    ApplyXmtUndo,
)
from convert.adapters.solidworks.Archive.Partition.History.CheckMarkChain import (
    CheckMarkChain,
)
from convert.adapters.solidworks.Archive.Partition.History.CheckUndoCounts import (
    CheckUndoCounts,
)
from convert.adapters.solidworks.Archive.Partition.History.CheckUndoGraph import (
    CheckUndoGraph,
)
from convert.adapters.solidworks.Archive.Partition.History.ReadHistFrames import (
    ReadHistFrames,
)
from convert.adapters.solidworks.Archive.Partition.History.ReadXmtDeltaMut import (
    ReadXmtDeltaMut,
)
from convert.adapters.solidworks.Archive.Partition.History.XmtStage import XmtStage
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# previous state application follows actual controller identities and their mark order
def ReadXmtStages(
    DataValue: bytes, NodesValue: Mapping[int, XmtNode], Selectors: tuple[int, ...]
) -> tuple[XmtStage, ...]:
    CheckUndoGraph(NodesValue)
    Expected = (1, *Selectors)
    RootValue, MarksValue, DeltasValue = ReadHistFrames(
        DataValue, NodesValue, ReadXmtDeltaMut, MarkLimit=min(len(Expected), 4096)
    )
    Current = CheckMarkChain(NodesValue, RootValue, MarksValue, DeltasValue)
    if len(MarksValue) != len(Expected):
        raise ValueError("rollback mark inventory differs from its archive controllers")
    Reserved = {RootValue.IndexValue, *MarksValue}
    StepsValue: list[XmtStage] = []
    NextIndex = Current.IndexValue
    for MarkId in reversed(Expected):
        MarkValue = MarksValue.get(NextIndex)
        if (
            MarkValue is None
            or MarkValue.Integer("id") != MarkId
            or MarkValue.Integer("first_following")
            != (StepsValue[-1].MarkValue.IndexValue if StepsValue else 0)
        ):
            raise ValueError("rollback mark differs from its actual controller")
        DeltaValue = DeltasValue.get(NextIndex)
        CheckUndoCounts(MarkValue, DeltaValue)
        StepsValue.append(XmtStage(MarkValue, NodesValue, DeltaValue))
        if DeltaValue is not None:
            NodesValue = ApplyXmtUndo(NodesValue, DeltaValue, Reserved)
        NextIndex = MarkValue.Integer("preceding")
    if NextIndex:
        raise ValueError("initial rollback mark has a foreign predecessor")
    return tuple(StepsValue)
