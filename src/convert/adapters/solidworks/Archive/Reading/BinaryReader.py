from dataclasses import dataclass as DataClass


# native stream readers need one bounded cursor for all scalar and object fields
@DataClass(slots=True)
class BinaryReader:
    BytesValue: bytes
    OffsetValue: int = 0
    LimitValue: int | None = None

    # nested cursors require an absolute window inside the shared buffer
    def __post_init__(self) -> None:
        if self.LimitValue is None:
            return
        if not 0 <= self.OffsetValue <= self.LimitValue <= len(self.BytesValue):
            raise ValueError("SOLIDWORKS archive cursor has an invalid window")

    # graph callbacks need the current position without knowing cursor storage
    def GetOffset(self) -> int:
        return self.OffsetValue

    # prefix codecs must obey the same limit as scalar reads
    def GetEnd(self) -> int:
        return len(self.BytesValue) if self.LimitValue is None else self.LimitValue

    # count validation needs the exact remaining space in the current window
    def GetRemaining(self) -> int:
        return self.GetEnd() - self.OffsetValue

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
