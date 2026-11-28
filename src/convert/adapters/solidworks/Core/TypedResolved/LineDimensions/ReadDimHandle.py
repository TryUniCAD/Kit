from convert.adapters.solidworks.Core.TypedResolved.Lines.LineIndex import LineIndex
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# local entity handles must preserve their concrete type and exact short or extended index namespace
def ReadDimHandle(HandleValue: object, ClassName: str) -> int:
    Handle = RequireNative(HandleValue, ClassName)
    FieldsValue = Handle.FieldsValue
    if FieldsValue.get("f1c") != -1 or FieldsValue.get("f08") != 0:
        raise ValueError("typed rectangle relation has a nonlocal entity handle")
    return LineIndex(FieldsValue, "idx", "f18", 30591)
