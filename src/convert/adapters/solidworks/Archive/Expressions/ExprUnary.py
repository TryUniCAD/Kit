from typing import cast as CastValue


# unary native operations retain arithmetic and truth meanings without dynamic function invocation
def ExprUnary(ActionValue: str, Value: object) -> object:
    match ActionValue:
        case "USub":
            return -CastValue(int | float, Value)
        case "UAdd":
            return +CastValue(int | float, Value)
        case "Invert":
            return ~CastValue(int, Value)
        case "Not":
            return not Value
        case _:
            raise ValueError(f"unsupported native unary operation {ActionValue}")
