from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.Staging.SeekBinary import SeekBinary
from convert.adapters.Staging.SinkExtentMut import SinkExtentMut

# policy refusals explain the complete precondition regardless of the stream implementation
KWholeSinkError = (
    "standalone native output requires an empty seekable binary stream at position zero"
)


# checking both cursor and extent refuses a prefix or stale tail without reading or truncating either
def CheckWholeSink(TargetValue: KTargetType) -> SeekBinary:
    if not IsBinaryTarget(TargetValue) or not isinstance(TargetValue, SeekBinary):
        raise ValueError(KWholeSinkError)
    try:
        IsEmpty = (
            TargetValue.seekable()
            and TargetValue.writable()
            and TargetValue.tell() == 0
            and SinkExtentMut(TargetValue) == 0
        )
    except (OSError, TypeError, ValueError) as ErrorInfo:
        raise ValueError(KWholeSinkError) from ErrorInfo
    if not IsEmpty:
        raise ValueError(KWholeSinkError)
    return TargetValue
