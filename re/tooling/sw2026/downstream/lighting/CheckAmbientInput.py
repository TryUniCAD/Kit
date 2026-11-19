from math import isfinite as IsFinite


# authored lighting must be explicit and bounded without borrowing the session environment vector
def CheckAmbientInput(
    NameValue: str,
    ExternalName: str,
    AmbientValue: float,
    DiffuseValue: float,
    SpecularValue: float,
    ColourValue: int,
) -> None:
    if any(
        type(Value) is not str or not Value or "\x00" in Value
        for Value in (NameValue, ExternalName)
    ):
        raise ValueError("ambient names must be explicit nonempty native text")
    if any(
        type(Value) is not float or not IsFinite(Value) or not 0.0 <= Value <= 1.0
        for Value in (AmbientValue, DiffuseValue, SpecularValue)
    ):
        raise ValueError("authored light coefficients must be finite unit scalars")
    if type(ColourValue) is not int or not 0 <= ColourValue <= 0xFFFFFF:
        raise ValueError("authored ambient colour must be a 24 bit COLORREF")
