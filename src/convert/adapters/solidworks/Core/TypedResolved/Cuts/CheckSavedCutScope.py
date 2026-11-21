from typing import Literal

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckCutWrapper import (
    CheckCutWrapper,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSaveScope import ReadSaveScope


# a saved body selection must agree with the consumed atom without inferring an unstored selection mode
def CheckCutScope(
    RootValue: ArchiveNode,
    BossValue: ArchiveNode,
    CutValue: ArchiveNode,
    AtomId: int,
    *,
    StockScope: Literal[0] | None = None,
) -> int:
    ScopeValue = ReadSaveScope(BossValue, CutValue, StockScope)
    if ScopeValue:
        CheckCutWrapper(RootValue, BossValue, CutValue, AtomId)
    return ScopeValue


# hash pinned through cut readers still import the original saved scope check
CheckSavedCutScope = CheckCutScope
