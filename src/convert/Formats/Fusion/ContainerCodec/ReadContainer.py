from collections.abc import Callable

from convert.Formats.Fusion.ContainerCodec.Model.FusionContainer import FusionContainer
from convert.Formats.Fusion.ContainerCodec.ReadIndexed import ReadIndexed


# archive inspection needs validated streams without retaining segment indexes
def ReadContainer(
    Payload: bytes, InflateZstd: Callable[[bytes, int], bytes] | None = None
) -> FusionContainer:
    Container, _ = ReadIndexed(Payload, InflateZstd, KeepIndexes=False)
    return Container
