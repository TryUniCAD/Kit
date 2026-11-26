from convert.adapters.solidworks.Archive.Construction.Model.EmptyBodyProps import (
    EmptyBodyProps,
)
from convert.adapters.solidworks.Archive.Construction.Model.EmptyRootRows import (
    EmptyRootRows,
)
from convert.adapters.solidworks.Archive.Construction.Model.ModelArrays import (
    KModelArrays,
    KModelLists,
)


# all common containers must be derived from actual empty collections rather than shared captured payloads
def MakeModelArrays() -> dict[str, object]:
    FieldsValue: dict[str, object] = {}
    for CountName, ArrayName in KModelArrays:
        ItemsValue: tuple[object, ...] = ()
        FieldsValue[ArrayName], FieldsValue[CountName] = ItemsValue, len(ItemsValue)
    FieldsValue.update({FieldName: EmptyRootRows() for FieldName in KModelLists})
    FieldsValue["fdd0"] = EmptyBodyProps(False)
    return FieldsValue
