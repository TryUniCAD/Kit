from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockRef import (
    ReadStockRef,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import (
    ReadSingleNode,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a matching numeric feature key cannot replace the actual stock reference shared with its chooser
def CheckStockFace(WrapperValue: ArchiveNode, StockValue: ArchiveNode) -> None:
    Fields = WrapperValue.FieldsValue
    Component = RequireNative(Fields.get("f58"), "moUnitComponent_c")
    WrapperRef = ReadStockRef(RequireNative(Fields.get("ff0")), StockValue, 3)
    Chooser = NativeRecord(StockValue.FieldsValue.get("f4a8"))
    if Component.FieldsValue.get("has_ext") != 0 or Chooser.get("f68") is not StockValue:
        raise ValueError("two stock face carrier has alternate component or chooser ownership")
    Choice = ReadSingleNode(Chooser.get("f48"), "moPerBodyChooserData_c")
    Faces = NativeRecord(Choice.FieldsValue.get("f08"))
    RowsValue = NativeRows(Faces.get("items"))
    if Faces.get("n") != 2 or len(RowsValue) != 2 or any(
        ReadStockRef(RequireNative(RowValue.get("o")), StockValue, 4) is not WrapperRef
        for RowValue in RowsValue
    ):
        raise ValueError("two stock face carrier is detached from the actual producer chooser")
