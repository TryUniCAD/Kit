from collections.abc import Callable
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteArrayMut import (
    WriteArrayMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteBooleanMut import (
    WriteBooleanMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteBranchMut import (
    WriteBranchMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteBytesMut import (
    WriteBytesMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteCachesMut import (
    WriteCachesMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteControlMut import (
    WriteControlMut,
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
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNestedMut import (
    WriteNestedMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNormalMut import (
    WriteNormalMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteOwnedMut import (
    WriteOwnedMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WritePackedMut import (
    WritePackedMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WritePresentMut import (
    WritePresentMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteRepeatMut import (
    WriteRepeatMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSectionMut import (
    WriteSectionMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteValidateMut import (
    WriteValidMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteValueMut import (
    WriteValueMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteVirtualMut import (
    WriteVirtualMut,
)

# both archive directions extend through the same explicit field vocabulary without document programs
KWriteActions: MappingProxyType[str, Callable[[WriteFrame, NativeField], None]] = (
    MappingProxyType(
        {
            "Scalar": WriteValueMut,
            "Text": WriteValueMut,
            "Node": WriteValueMut,
            "Base": WriteNestedMut,
            "Embed": WriteNestedMut,
            "Array": WriteArrayMut,
            "Boolean": WriteBooleanMut,
            "Present": WritePresentMut,
            "Branch": WriteBranchMut,
            "Context": WriteControlMut,
            "Mask": WriteControlMut,
            "Virtual": WriteVirtualMut,
            "Validate": WriteValidMut,
            "Section": WriteSectionMut,
            "Direct": WriteDirectMut,
            "Bytes": WriteBytesMut,
            "Length": WriteLengthMut,
            "Repeat": WriteRepeatMut,
            "Normalize": WriteNormalMut,
            "GhostCount": WriteGhostMut,
            "MassCaches": WriteCachesMut,
            "BBoxCache": WriteCachesMut,
            "DirectNode": WriteOwnedMut,
            "Packed": WritePackedMut,
        }
    )
)
