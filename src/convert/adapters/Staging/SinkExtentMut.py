from os import SEEK_END as KSeekEnd
from os import SEEK_SET as KSeekSet

from convert.adapters.Staging.SeekBinary import SeekBinary


# seek to end checks the true output extent while returning the caller to its original position
def SinkExtentMut(TargetValue: SeekBinary) -> int:
    Position = TargetValue.tell()
    try:
        Extent = TargetValue.seek(0, KSeekEnd)
    finally:
        Restored = TargetValue.seek(Position, KSeekSet)
    if (
        type(Extent) is not int
        or Extent < 0
        or Restored != Position
        or TargetValue.tell() != Position
    ):
        raise ValueError(
            "binary stream did not report its extent or restore its cursor"
        )
    return Extent
