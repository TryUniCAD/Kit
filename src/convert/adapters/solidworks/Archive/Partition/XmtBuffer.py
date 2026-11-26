# bounded byte ownership keeps malformed kernel fields from crossing their declared payload
class XmtBuffer:

    # payload storage must be isolated from record state and external file access
    def __init__(self, DataValue: bytes) -> None:
        super().__init__()
        if len(DataValue) > 16777216:
            raise ValueError("current kernel profile exceeds its read bound")
        self.DataValue = DataValue
        self.OffsetValue = 0

    # exact extents prevent malformed arrays from borrowing following native records
    def TakeBytes(self, CountValue: int) -> bytes:
        EndValue = self.OffsetValue + CountValue
        if CountValue < 0 or EndValue > len(self.DataValue):
            raise ValueError("current kernel record is truncated")
        ResultValue = self.DataValue[self.OffsetValue : EndValue]
        self.OffsetValue = EndValue
        return ResultValue

    # format markers must match rather than silently advancing over unknown grammar
    def ExpectBytes(self, Expected: bytes) -> None:
        if self.TakeBytes(len(Expected)) != Expected:
            raise ValueError("current kernel framing differs")
