from typing import cast as CastValue


# field comparisons distinguish identity and numeric order without accepting document supplied callables
def IsValueCompared(ActionValue: str, LeftValue: object, RightValue: object) -> bool:
    LeftNumber, RightNumber = CastValue(int | float, LeftValue), CastValue(
        int | float, RightValue
    )
    match ActionValue:
        case "Eq":
            return LeftValue == RightValue
        case "NotEq":
            return LeftValue != RightValue
        case "Lt":
            return LeftNumber < RightNumber
        case "LtE":
            return LeftNumber <= RightNumber
        case "Gt":
            return LeftNumber > RightNumber
        case "GtE":
            return LeftNumber >= RightNumber
        case "Is":
            return LeftValue is RightValue
        case "IsNot":
            return LeftValue is not RightValue
    raise ValueError(f"unsupported native comparison {ActionValue}")
