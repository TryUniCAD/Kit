from typing import Literal

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import ReadSingleNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord


# the ordinary scope word and chooser alias are independent of each selector layout
def ReadSaveScope(
    BossValue: ArchiveNode,
    CutValue: ArchiveNode,
    StockScope: Literal[0, 1] | None,
) -> int:
    Fields = CutValue.FieldsValue
    ScopeValue = Fields.get("f544")
    if (
        type(ScopeValue) is not int
        or ScopeValue not in (0, 1)
        or BossValue.FieldsValue.get("f544") != (ScopeValue if StockScope is None else StockScope)
        or Fields.get("has_f4c0") != 1
        or Fields.get("has_f548") != ScopeValue
    ):
        raise ValueError("cut body scope is outside the witnessed saved profiles")
    Chooser = NativeRecord(Fields.get("f4c0"))
    ReadSingleNode(Chooser.get("f48"), "moPerBodyChooserData_c")
    if Chooser.get("f68") is not CutValue:
        raise ValueError("cut body chooser does not alias its owning feature")
    return ScopeValue
