from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import (
    ReadSingleNode,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a saved body selection must agree with the consumed atom without inferring an unstored selection mode
def CheckSavedCutScope(
    RootValue: ArchiveNode, BossValue: ArchiveNode, CutValue: ArchiveNode, AtomId: int
) -> int:
    Fields = CutValue.FieldsValue
    ScopeValue = Fields.get("f544")
    if (
        type(ScopeValue) is not int
        or ScopeValue not in (0, 1)
        or BossValue.FieldsValue.get("f544") != ScopeValue
        or Fields.get("has_f4c0") != 1
        or Fields.get("has_f548") != ScopeValue
    ):
        raise ValueError("cut body scope is outside the witnessed saved profiles")
    Chooser = NativeRecord(Fields.get("f4c0"))
    ReadSingleNode(Chooser.get("f48"), "moPerBodyChooserData_c")
    if Chooser.get("f68") is not CutValue:
        raise ValueError("cut body chooser does not alias its owning feature")
    if ScopeValue:
        Wrapper = ReadSingleNode(Fields.get("f548"), "moCompSolidBody_c").FieldsValue
        Component = RequireNative(Wrapper.get("f58"), "moUnitComponent_c")
        Lineage = NativeRows(Wrapper.get("f110"))
        if (
            Wrapper.get("f108") != NativeNodeId(BossValue)
            or Wrapper.get("f18") != AtomId
            or Wrapper.get("f1c") != AtomId
            or Wrapper.get("n110") != 1
            or tuple(Row.get("v") for Row in Lineage) != (AtomId,)
            or Component.FieldsValue.get("owner") is not RootValue
        ):
            raise ValueError(
                "cut selection wrapper differs from the consumed boss atom"
            )
    return ScopeValue
