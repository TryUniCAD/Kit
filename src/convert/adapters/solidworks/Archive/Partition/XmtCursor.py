from struct import pack as PackValue
from struct import unpack as UnpackValue

from convert.adapters.solidworks.Archive.Partition.XmtBuffer import XmtBuffer


# bounded current schema decoding must reject truncated or noncanonical native references
class XmtCursor(XmtBuffer):

    # each payload owns its schema state and cannot inherit unrelated record definitions
    def __init__(self, DataValue: bytes) -> None:
        super().__init__(DataValue)
        self.SeenKinds: set[int] = set()
        self.ExpectBytes(PackValue(">HI", 239, 0))

    # short class identifiers are independent from transmitted object indices
    def ReadKind(self) -> int:
        return int(UnpackValue(">H", self.TakeBytes(2))[0])

    # variable arrays declare their element count before the native record index
    def ReadCount(self) -> int:
        CountValue = int(UnpackValue(">I", self.TakeBytes(4))[0])
        if CountValue > len(self.DataValue) - self.OffsetValue:
            raise ValueError("current kernel array exceeds its payload")
        return CountValue

    # neutral provenance must preserve the actual native transmit index domain
    def ReadIndex(self) -> int:
        FirstValue = int(UnpackValue(">h", self.TakeBytes(2))[0])
        if FirstValue > 0:
            return FirstValue - 1
        if FirstValue in (0, -32768):
            raise ValueError("invalid current kernel reference")
        WideValue = self.ReadKind() * 32767 - FirstValue - 1
        if WideValue < 32767:
            raise ValueError("noncanonical current kernel reference")
        return WideValue

    # a complete payload cannot leave an unclassified native tail behind
    def FinishRead(self) -> None:
        if self.ReadIndex() or self.OffsetValue != len(self.DataValue):
            raise ValueError("current kernel terminator differs")
