from __future__ import annotations as Annotations

# xxh32 constants come from the published algorithm and never encode file bytes
KPrimeOne = 2654435761
KPrimeTwo = 2246822519
KPrimeThree = 3266489917
KPrimeFour = 668265263
KPrimeFive = 374761393

# the mask keeps every accumulator inside the published word width
KWordMask = 0xFFFFFFFF


# the header seal uses the published xxh32 digest over the nx header region
def HashXxh(DataValue: bytes, SeedValue: int = 0) -> int:
    Length = len(DataValue)
    Position = 0
    if Length >= 16:
        AccOne = (SeedValue + KPrimeOne + KPrimeTwo) & KWordMask
        AccTwo = (SeedValue + KPrimeTwo) & KWordMask
        AccThree = SeedValue & KWordMask
        AccFour = (SeedValue - KPrimeOne) & KWordMask
        while Position <= Length - 16:
            AccOne = Round(AccOne, LaneWord(DataValue, Position))
            AccTwo = Round(AccTwo, LaneWord(DataValue, Position + 4))
            AccThree = Round(AccThree, LaneWord(DataValue, Position + 8))
            AccFour = Round(AccFour, LaneWord(DataValue, Position + 12))
            Position += 16
        AccValue = (
            Rotate(AccOne, 1)
            + Rotate(AccTwo, 7)
            + Rotate(AccThree, 12)
            + Rotate(AccFour, 18)
        ) & KWordMask
    else:
        AccValue = (SeedValue + KPrimeFive) & KWordMask
    AccValue = (AccValue + Length) & KWordMask
    while Position <= Length - 4:
        AccValue = Rotate(
            (AccValue + LaneWord(DataValue, Position) * KPrimeThree) & KWordMask, 17
        )
        AccValue = (AccValue * KPrimeFour) & KWordMask
        Position += 4
    while Position < Length:
        AccValue = Rotate((AccValue + DataValue[Position] * KPrimeFive) & KWordMask, 11)
        AccValue = (AccValue * KPrimeOne) & KWordMask
        Position += 1
    return FinalMix(AccValue)


# one striped lane applies the published two prime multiplications
def Round(AccValue: int, LaneValue: int) -> int:
    Mixed = (AccValue + LaneValue * KPrimeTwo) & KWordMask
    return (Rotate(Mixed, 13) * KPrimeOne) & KWordMask


# the avalanche step spreads low bits across the final word
def FinalMix(AccValue: int) -> int:
    AccValue ^= AccValue >> 15
    AccValue = (AccValue * KPrimeTwo) & KWordMask
    AccValue ^= AccValue >> 13
    AccValue = (AccValue * KPrimeThree) & KWordMask
    AccValue ^= AccValue >> 16
    return AccValue & KWordMask


# lane reads stay explicit because the digest depends on little endian words
def LaneWord(DataValue: bytes, Offset: int) -> int:
    return int.from_bytes(DataValue[Offset : Offset + 4], "little")


# rotation keeps the published bit order for mixed accumulators
def Rotate(Value: int, RotateBits: int) -> int:
    return ((Value << RotateBits) | (Value >> (32 - RotateBits))) & KWordMask
