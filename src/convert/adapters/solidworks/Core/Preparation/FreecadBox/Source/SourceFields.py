# an unsupported source condition must abort before any lowering is attempted
def RequireBox(Condition: object, MessageValue: str) -> None:
    if not Condition:
        raise ValueError(MessageValue)


# source property text remains literal and cannot be supplied by coercion
def ReadBoxString(Value: object) -> str:
    if not isinstance(Value, str):
        raise ValueError("FreeCAD box expected a literal source string")
    return Value
