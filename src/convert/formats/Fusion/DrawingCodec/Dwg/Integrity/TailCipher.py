from decimal import Decimal, getcontext
from struct import pack as PackFields
from struct import unpack as UnpackFields

KWordCount = 18 + 4 * 256
KKey = bytes.fromhex("e1a43cf0aa69e0e31755c78100d809de")
KMask = 0xFFFFFFFF


def PiWords(WordCount: int) -> tuple[int, ...]:
    HexCount = WordCount * 8
    getcontext().prec = int(HexCount * 1.20412) + 80
    SqrtTerm = 426880 * Decimal(10005).sqrt()
    Multiplier = 1
    Linear = 13591409
    Power = 1
    Index = 6
    Total = Decimal(Linear)
    Terms = int(getcontext().prec / 13.5) + 20
    for Step in range(1, Terms):
        Multiplier = (Index**3 - 16 * Index) * Multiplier // Step**3
        Linear += 545140134
        Power *= -262537412640768000
        Total += Decimal(Multiplier * Linear) / Power
        Index += 12
    PiValue = SqrtTerm / Total
    Scaled = int((PiValue - 3) * (Decimal(16) ** HexCount))
    Text = format(Scaled, "0%dx" % HexCount)
    return tuple(int(Text[Start : Start + 8], 16) for Start in range(0, HexCount, 8))


def KeySchedule(KeyValue: bytes) -> tuple[list[int], list[int], list[int], list[int], list[int]]:
    Words = PiWords(KWordCount)
    PValue = list(Words[:18])
    S0Value = list(Words[18 : 18 + 256])
    S1Value = list(Words[18 + 256 : 18 + 512])
    S2Value = list(Words[18 + 512 : 18 + 768])
    S3Value = list(Words[18 + 768 : 18 + 1024])
    KeyIndex = 0
    for Index in range(18):
        Data = 0
        for _ in range(4):
            Data = ((Data << 8) | KeyValue[KeyIndex]) & KMask
            KeyIndex = (KeyIndex + 1) % len(KeyValue)
        PValue[Index] ^= Data
    LeftValue = 0
    RightValue = 0
    for Index in range(0, 18, 2):
        LeftValue, RightValue = EncryptBlock(LeftValue, RightValue, PValue, S0Value, S1Value, S2Value, S3Value)
        PValue[Index], PValue[Index + 1] = LeftValue, RightValue
    for BoxValue in (S0Value, S1Value, S2Value, S3Value):
        for Index in range(0, 256, 2):
            LeftValue, RightValue = EncryptBlock(LeftValue, RightValue, PValue, S0Value, S1Value, S2Value, S3Value)
            BoxValue[Index], BoxValue[Index + 1] = LeftValue, RightValue
    return PValue, S0Value, S1Value, S2Value, S3Value


def FuncValue(Value: int, S0Value: list[int], S1Value: list[int], S2Value: list[int], S3Value: list[int]) -> int:
    AValue = (Value >> 24) & 0xFF
    BValue = (Value >> 16) & 0xFF
    CValue = (Value >> 8) & 0xFF
    DValue = Value & 0xFF
    Result = (S0Value[AValue] + S1Value[BValue]) & KMask
    Result ^= S2Value[CValue]
    return (Result + S3Value[DValue]) & KMask


def EncryptBlock(
    LeftValue: int,
    RightValue: int,
    PValue: list[int],
    S0Value: list[int],
    S1Value: list[int],
    S2Value: list[int],
    S3Value: list[int],
) -> tuple[int, int]:
    for Index in range(16):
        LeftValue ^= PValue[Index]
        RightValue ^= FuncValue(LeftValue, S0Value, S1Value, S2Value, S3Value)
        LeftValue, RightValue = RightValue, LeftValue
    LeftValue, RightValue = RightValue, LeftValue
    RightValue ^= PValue[16]
    LeftValue ^= PValue[17]
    return LeftValue & KMask, RightValue & KMask


def DecryptBlock(
    LeftValue: int,
    RightValue: int,
    PValue: list[int],
    S0Value: list[int],
    S1Value: list[int],
    S2Value: list[int],
    S3Value: list[int],
) -> tuple[int, int]:
    for Index in range(17, 1, -1):
        LeftValue ^= PValue[Index]
        RightValue ^= FuncValue(LeftValue, S0Value, S1Value, S2Value, S3Value)
        LeftValue, RightValue = RightValue, LeftValue
    LeftValue, RightValue = RightValue, LeftValue
    RightValue ^= PValue[1]
    LeftValue ^= PValue[0]
    return LeftValue & KMask, RightValue & KMask


KState = KeySchedule(KKey)


def EncryptBytes(DataValue: bytes) -> bytes:
    LeftValue, RightValue = UnpackFields(">II", DataValue)
    LeftValue, RightValue = EncryptBlock(LeftValue, RightValue, *KState)
    return PackFields(">II", LeftValue, RightValue)


def DecryptBytes(DataValue: bytes) -> bytes:
    LeftValue, RightValue = UnpackFields(">II", DataValue)
    LeftValue, RightValue = DecryptBlock(LeftValue, RightValue, *KState)
    return PackFields(">II", LeftValue, RightValue)
