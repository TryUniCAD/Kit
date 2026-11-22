from typing import cast as CastValue


# unary native operations retain arithmetic and truth meanings without dynamic function invocation
def ExprUnary(ActionValue: str, Value: object) -> object:
    if ActionValue == "USub":
        return -CastValue(int | float, Value)
    if ActionValue == "UAdd":
        return +CastValue(int | float, Value)
    if ActionValue == "Invert":
        return ~CastValue(int, Value)
    if ActionValue == "Not":
        return not Value
    raise ValueError(f"unsupported native unary operation {ActionValue}")
