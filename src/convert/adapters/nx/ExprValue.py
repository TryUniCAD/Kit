from __future__ import annotations

# nx stores an expression value as a sixteen bit float with a fixed tag nibble
KValueTag = 0x50
KValueScale = 4096
KValueMask = 0x0FFF
KCompactLimit = 2
KSmallest = 0.75


def EncodeValue(Value: float) -> int:
    if Value <= 0:
        raise ValueError("NX expression values must be positive")
    if Value < KSmallest:
        raise ValueError(
            "NX expression values below 0.75 use a compact form the writer cannot emit"
        )
    if float(Value).is_integer() and Value <= KCompactLimit:
        return int(Value)
    Exponent = 1
    while (2**Exponent) <= Value:
        Exponent += 1
    Fraction = Value / (2 ** (Exponent - 1)) - 1
    return int((Exponent << 12) | (KValueTag + round(Fraction * KValueScale)))


def DecodeValue(Handle: int) -> float:
    if Handle <= 0x100:
        return float(Handle)
    Exponent = Handle >> 12
    Fraction = ((Handle & KValueMask) - KValueTag) / KValueScale
    return float((2 ** (Exponent - 1)) * (1 + Fraction))
