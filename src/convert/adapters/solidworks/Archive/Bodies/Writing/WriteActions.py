from convert.adapters.solidworks.Archive.Bodies.Writing.WritePatField import (
    WritePatField,
)
from collections.abc import Callable
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteArrayMut import (
    WriteArrayMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteBoundsMut import (
    WriteBoundsMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteBranchMut import (
    WriteBranchMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteBooleanMut import (
    WriteBooleanMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteBytesMut import (
    WriteBytesMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteContextMut import (
    WriteContextMut,
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
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteDirectMut import (
    WriteDirectMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteGhostMut import (
    WriteGhostMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteLengthMut import (
    WriteLengthMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteMassMut import (
    WriteMassMut,
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
            "Boolean": WriteBooleanMut,
            "Bytes": WriteBytesMut,
            "Context": WriteContextMut,
            "Mask": WritePatField,
            "Validate": WritePatField,
            "DirectNode": WriteOwnedMut,
            "Present": WritePresentMut,
            "Packed": WritePackedMut,
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
            "MassCaches": WriteMassMut,
            "BBoxCache": WriteBoundsMut,
        }
    )
)
