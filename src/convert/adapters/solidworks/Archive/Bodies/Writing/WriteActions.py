from collections.abc import Callable
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteArrayMut import (
    WriteArrayMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNestedMut import (
    WriteNestedMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteValueMut import (
    WriteValueMut,
)

# both archive directions share field ownership without document specific fallback logic
KWriteActions: MappingProxyType[str, Callable[[WriteFrame, NativeField], None]] = (
    MappingProxyType(
        {
            "Scalar": WriteValueMut,
            "Text": WriteValueMut,
            "Node": WriteValueMut,
            "Embed": WriteNestedMut,
            "Array": WriteArrayMut,
        }
    )
)
