from typing import cast as CastValue


# native arithmetic rules need their numeric behavior without unrestricted callable values
def ExprBinary(ActionValue: str, LeftValue: object, RightValue: object) -> object:
    LeftNumber, RightNumber = CastValue(int | float, LeftValue), CastValue(
        int | float, RightValue
    )
    if ActionValue == "Add":
        return LeftNumber + RightNumber
    if ActionValue == "Sub":
        return LeftNumber - RightNumber
    if ActionValue == "Mult":
        return LeftNumber * RightNumber
    if ActionValue == "FloorDiv":
        return LeftNumber // RightNumber
    if ActionValue == "BitAnd":
        return CastValue(int, LeftValue) & CastValue(int, RightValue)
    if ActionValue == "BitOr":
        return CastValue(int, LeftValue) | CastValue(int, RightValue)
    if ActionValue == "BitXor":
        return CastValue(int, LeftValue) ^ CastValue(int, RightValue)
    if ActionValue == "LShift":
        return CastValue(int, LeftValue) << CastValue(int, RightValue)
    if ActionValue == "RShift":
        return CastValue(int, LeftValue) >> CastValue(int, RightValue)
    raise ValueError(f"unsupported native binary operation {ActionValue}")
