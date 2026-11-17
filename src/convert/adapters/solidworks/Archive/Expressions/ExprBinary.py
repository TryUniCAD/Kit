from typing import cast as CastValue


# native arithmetic rules need their numeric behavior without unrestricted callable values
def ExprBinary(ActionValue: str, LeftValue: object, RightValue: object) -> object:
    LeftNumber, RightNumber = CastValue(int | float, LeftValue), CastValue(
        int | float, RightValue
    )
    match ActionValue:
        case "Add":
            return LeftNumber + RightNumber
        case "Sub":
            return LeftNumber - RightNumber
        case "Mult":
            return LeftNumber * RightNumber
        case "FloorDiv":
            return LeftNumber // RightNumber
        case "BitAnd":
            return CastValue(int, LeftValue) & CastValue(int, RightValue)
        case "BitOr":
            return CastValue(int, LeftValue) | CastValue(int, RightValue)
        case "BitXor":
            return CastValue(int, LeftValue) ^ CastValue(int, RightValue)
        case "LShift":
            return CastValue(int, LeftValue) << CastValue(int, RightValue)
        case "RShift":
            return CastValue(int, LeftValue) >> CastValue(int, RightValue)
        case _:
            raise ValueError(f"unsupported native binary operation {ActionValue}")
