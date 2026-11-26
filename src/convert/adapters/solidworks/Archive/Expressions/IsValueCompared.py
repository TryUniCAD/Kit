from typing import cast as CastValue


# field comparisons distinguish identity and numeric order without accepting document supplied callables
def IsValueCompared(ActionValue: str, LeftValue: object, RightValue: object) -> bool:
    LeftNumber, RightNumber = CastValue(int | float, LeftValue), CastValue(
        int | float, RightValue
    )
    if ActionValue == "Eq":
        return LeftValue == RightValue
    if ActionValue == "NotEq":
        return LeftValue != RightValue
    if ActionValue == "Lt":
        return LeftNumber < RightNumber
    if ActionValue == "LtE":
        return LeftNumber <= RightNumber
    if ActionValue == "Gt":
        return LeftNumber > RightNumber
    if ActionValue == "GtE":
        return LeftNumber >= RightNumber
    if ActionValue == "Is":
        return LeftValue is RightValue
    if ActionValue == "IsNot":
        return LeftValue is not RightValue
    raise ValueError(f"unsupported native comparison {ActionValue}")
