from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# singleton curve and sketch values must come from their actual counted row
def ReadSwRow(
    OwnerValue: object,
    CountName: str = "n",
    ItemsName: str = "items",
    ValueName: str = "o",
) -> object:
    FieldsValue = NativeRecord(OwnerValue)
    RowsValue = NativeRows(FieldsValue.get(ItemsName))
    if FieldsValue.get(CountName) != 1 or len(RowsValue) != 1:
        raise ValueError("SOLIDWORKS sweep requires one actual " + ItemsName + " row")
    return RowsValue[0].get(ValueName)
