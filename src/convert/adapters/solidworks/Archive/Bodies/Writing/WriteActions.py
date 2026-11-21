from collections.abc import Callable
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteArrayMut import (
    WriteArrayMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteBranchMut import (
    WriteBranchMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteCachesMut import (
    WriteCachesMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteDirectMut import (
    WriteDirectMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteGhostMut import (
    WriteGhostMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteLengthMut import (
    WriteLengthMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNormalMut import (
    WriteNormalMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSectionMut import (
    WriteSectionMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteVirtualMut import (
    WriteVirtualMut,
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
            "Base": WriteNestedMut,
            "Embed": WriteNestedMut,
            "Array": WriteArrayMut,
            "Branch": WriteBranchMut,
            "Length": WriteLengthMut,
            "Repeat": WriteArrayMut,
            "Normalize": WriteNormalMut,
            "Virtual": WriteVirtualMut,
            "Section": WriteSectionMut,
            "Direct": WriteDirectMut,
            "GhostCount": WriteGhostMut,
            "MassCaches": WriteCachesMut,
            "BBoxCache": WriteCachesMut,
        }
    )
)
