from dataclasses import dataclass as DataClass


# native stream readers need one bounded cursor for all scalar and object fields
@DataClass(slots=True)
class BinaryReader:
    BytesValue: bytes
    OffsetValue: int = 0

    # graph callbacks need the current position without knowing cursor storage
    def GetOffset(self) -> int:
        return self.OffsetValue

    # count validation needs the exact remaining stream length
    def GetRemaining(self) -> int:
        return len(self.BytesValue) - self.OffsetValue

    # all field reads must fail at a real record boundary on truncation
    def TakeBytes(self, ByteCount: int) -> bytes:
        if not 0 <= ByteCount <= self.GetRemaining():
            raise ValueError(
                f"truncated SOLIDWORKS archive field at {self.OffsetValue}"
            )
        StartValue = self.OffsetValue
        self.OffsetValue += ByteCount
        return self.BytesValue[StartValue : self.OffsetValue]

    # structural prefix and flags are unsigned until an owner requires signed values
    def ReadUnsigned(self, ByteCount: int) -> int:
        return int.from_bytes(self.TakeBytes(ByteCount), "little")
