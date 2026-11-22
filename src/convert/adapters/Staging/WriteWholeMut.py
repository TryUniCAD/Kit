from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.Staging.CheckWholeSink import CheckWholeSink
from convert.adapters.Staging.SinkExtentMut import SinkExtentMut


# whole file acceptance follows the actual caller sink bounds before and after its only write
def WriteWholeMut(TargetValue: KTargetType, Payload: bytes) -> None:
    Output = CheckWholeSink(TargetValue)
    PayloadSize = len(Payload)
    WrittenCount = Output.write(Payload)
    if (
        WrittenCount != PayloadSize
        or Output.tell() != PayloadSize
        or SinkExtentMut(Output) != PayloadSize
    ):
        raise OSError("incomplete standalone destination write")
