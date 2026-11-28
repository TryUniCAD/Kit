from math import isfinite as IsFinite, nextafter as NextFloat


# the displayed millimetres may not multiply back to the original metre word
def ExactMm(Native: object, Display: float, *, Multiplied: bool = False) -> float:
    if type(Native) is not float or not IsFinite(Native):
        raise ValueError("SOLIDWORKS metre value is missing or not finite")
    DisplayValue = Native * 1000.0 if Multiplied else Native / 0.001
    if DisplayValue.hex() != Display.hex():
        raise ValueError("SOLIDWORKS metre value disagrees with its public length")
    Quotient = Native / 0.001
    if IsFinite(Quotient):
        Product = Quotient * 0.001
        if Product.hex() == Native.hex():
            return Quotient
        Neighbor = NextFloat(
            Quotient, float("inf") if Product < Native else -float("inf")
        )
        if (Neighbor * 0.001).hex() == Native.hex():
            return Neighbor
    raise ValueError("SOLIDWORKS metre value has no exact millimetre inverse")
