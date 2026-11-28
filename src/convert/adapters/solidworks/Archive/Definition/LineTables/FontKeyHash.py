from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# the selected native map hashes sampled utf16 units with its exact unsigned32 multiply then xor rule
def FontKeyHash(CategoryValue: str) -> int:
    NameValue = ReadStyleText(CategoryValue, "line font category")
    UnitBytes = NameValue.encode("utf-16-le")
    UnitCount = len(UnitBytes) // 2
    StepValue = (UnitCount * 0xCCCCCCCD >> 35) + 1
    HashValue = 0x811C9DC5
    for IndexValue in range(0, UnitCount, StepValue):
        UnitValue = int.from_bytes(
            UnitBytes[2 * IndexValue : 2 * IndexValue + 2], "little"
        )
        HashValue = ((HashValue * 0x1000193) ^ UnitValue) & 0xFFFFFFFF
    return HashValue
