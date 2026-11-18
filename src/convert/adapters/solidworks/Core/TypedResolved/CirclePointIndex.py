from collections.abc import Mapping


# compact sketch indices retain separate short and extended fields in the archive
def CirclePointIndex(FieldsValue: Mapping[str, object], FieldName: str) -> int:
    Value = FieldsValue.get(FieldName + "_s")
    if Value == 65535:
        Value = FieldsValue.get(FieldName)
    if type(Value) is not int:
        raise ValueError("typed circle has no point index")
    return Value
