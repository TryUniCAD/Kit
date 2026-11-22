from collections.abc import Callable
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadArrayMut import ReadArrayMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadBBoxMut import ReadBBoxMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadBooleanMut import (
    ReadBooleanMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadBranchMut import (
    ReadBranchMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadBytesMut import ReadBytesMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadContextMut import (
    ReadContextMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadDirectMut import (
    ReadDirectMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadGhostMut import ReadGhostMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadLengthMut import (
    ReadLengthMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadMassMut import ReadMassMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadNestedMut import (
    ReadNestedMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadNormalMut import (
    ReadNormalMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadOwnedMut import ReadOwnedMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadPresentMut import (
    ReadPresentMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadRepeatMut import (
    ReadRepeatMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadSectionMut import (
    ReadSectionMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadValueMut import ReadValueMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadVirtualMut import (
    ReadVirtualMut,
)

# field dispatch admits only the operations with shared body implementations
KReadActions: MappingProxyType[str, Callable[[ReadFrame, NativeField], None]] = (
    MappingProxyType(
        {
            "Scalar": ReadValueMut,
            "Text": ReadValueMut,
            "Node": ReadValueMut,
            "Section": ReadSectionMut,
            "Direct": ReadDirectMut,
            "DirectNode": ReadOwnedMut,
            "GhostCount": ReadGhostMut,
            "Base": ReadNestedMut,
            "Embed": ReadNestedMut,
            "Array": ReadArrayMut,
            "Context": ReadContextMut,
            "Present": ReadPresentMut,
            "Length": ReadLengthMut,
            "Repeat": ReadRepeatMut,
            "Branch": ReadBranchMut,
            "Virtual": ReadVirtualMut,
            "Bytes": ReadBytesMut,
            "Boolean": ReadBooleanMut,
            "MassCaches": ReadMassMut,
            "BBoxCache": ReadBBoxMut,
            "Normalize": ReadNormalMut,
        }
    )
)
