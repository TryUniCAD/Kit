from math import isfinite
from uuid import UUID


# source metadata scalars must preserve their native type instead of accepting coercion or precision loss
def ReadBlankScalar(TypeValue: object, Value: object) -> object:
    if TypeValue is type(None):
        if Value is not None:
            raise ValueError("blank metadata expected an absent owner")
        return None
    if TypeValue is float:
        if type(Value) is not float or not isfinite(Value):
            raise ValueError(
                "blank metadata floating owner is not finite native precision"
            )
        return Value
    if TypeValue is UUID:
        if type(Value) is not str:
            raise ValueError("blank metadata identity is not canonical UUID text")
        Identity = UUID(Value)
        if str(Identity) != Value or Identity.version != 4:
            raise ValueError(
                "blank metadata identity is outside the generated UUID4 profile"
            )
        return Identity
    if TypeValue is str or TypeValue is int or TypeValue is bool:
        if type(Value) is not TypeValue:
            raise ValueError(
                "blank metadata scalar type differs from its official owner"
            )
        return Value
    raise ValueError("blank metadata scalar owner is not supported")
