from typing import Protocol
from typing import runtime_checkable as RuntimeCheck

from convert.adapters.base.ContractTypes import BinaryWriter


# checking output extent needs cursor operations and never requires reading caller contents
@RuntimeCheck
class SeekBinary(BinaryWriter, Protocol):

    # unsupported sinks cannot establish the bounds of a standalone result
    def seekable(self) -> bool:
        raise TypeError("binary sink must report seekability")

    # a read only destination must fail before output is attempted
    def writable(self) -> bool:
        raise TypeError("binary sink must report writability")

    # the caller cursor is the actual publication start
    def tell(self) -> int:
        raise TypeError("binary sink must report its position")

    # seek exposes the logical end position without exposing stored data
    def seek(self, OffsetValue: int, WhenceValue: int = 0, /) -> int:
        raise TypeError("binary sink must expose its logical extent")
