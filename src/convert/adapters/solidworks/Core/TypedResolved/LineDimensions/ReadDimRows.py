from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# manager counts must match their ordered rows before unsupported dimension groups can be excluded
def ReadDimRows(
    FieldsValue: Mapping[str, object], CountName: str, ArrayName: str
) -> tuple[Mapping[str, object], ...]:
    RowsValue = NativeRows(FieldsValue.get(ArrayName))
    CountValue = FieldsValue.get(CountName)
    if type(CountValue) is not int or CountValue != len(RowsValue):
        raise ValueError("typed rectangle dimension count disagrees with owned rows")
    return RowsValue
