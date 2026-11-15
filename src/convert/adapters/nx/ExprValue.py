from __future__ import annotations

# nx stores an expression value as a sixteen bit float with a fixed tag nibble
KValueTag = 0x50

# needed so kvalue scale stays a single named source for the nx adapter
KValueScale = 4096

# needed so kvalue mask stays a single named source for the nx adapter
KValueMask = 0x0FFF

# needed so kcompact limit stays a single named source for the nx adapter
KCompactLimit = 2

# needed so ksmallest stays a single named source for the nx adapter
KSmallest = 0.75


# needed so encode value keeps its nx behaviour in one reviewable place
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


# needed so decode value keeps its nx behaviour in one reviewable place
def DecodeValue(Handle: int) -> float:
    if Handle <= 0x100:
        return float(Handle)
    Exponent = Handle >> 12
    Fraction = ((Handle & KValueMask) - KValueTag) / KValueScale
    return float((2 ** (Exponent - 1)) * (1 + Fraction))
