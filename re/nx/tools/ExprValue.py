from __future__ import annotations
import math
import sys

KTag = 0x50
KScale = 4096
KMantissaMask = 0x0FFF
KSmallLimit = 2


def Encode(Value: float) -> int:
    if Value > 0 and float(Value).is_integer() and Value <= KSmallLimit:
        return int(Value)
    if Value < 0.75:
        raise ValueError("nx uses a compact handle form below 0.75 that is not derived")
    Exponent = math.floor(math.log2(Value)) + 1
    Fraction = Value / (2 ** (Exponent - 1)) - 1
    return (Exponent << 12) | (KTag + round(Fraction * KScale))


def Decode(Handle: int) -> float:
    if Handle <= 0x100:
        return float(Handle)
    Exponent = Handle >> 12
    Fraction = ((Handle & KMantissaMask) - KTag) / KScale
    return (2 ** (Exponent - 1)) * (1 + Fraction)


def Main() -> int:
    Known = {
        0.75: 0x0850,
        3.0: 0x2850,
        3.25: 0x2A50,
        7.75: 0x3F50,
        10.0: 0x4450,
        12.5: 0x4950,
        13.5: 0x4B50,
        25.0: 0x5950,
        100.0: 0x7950,
    }
    Fails = 0
    for Value, Handle in Known.items():
        Encoded = Encode(Value)
        Decoded = Decode(Handle)
        Status = Encoded == Handle and abs(Decoded - Value) < 1e-9
        Fails += 0 if Status else 1
        print(f"{Value:8.3f} known {Handle:#06x} encoded {Encoded:#06x} decoded {Decoded:8.3f} {'ok' if Status else 'FAIL'}")
    for Value in (1.0, 2.0, 4.5, 6.0, 40.0, 250.0):
        print(f"roundtrip {Value:8.3f} -> {Encode(Value):#06x} -> {Decode(Encode(Value)):8.3f}")
    return 1 if Fails else 0


if __name__ == "__main__":
    raise SystemExit(Main())
