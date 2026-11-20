from convert.adapters.solidworks.Archive.Bodies.Reading.ReadPackedMut import (
    ReadPackedMut,
)
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
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadControlMut import (
    ReadControlMut,
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
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadNormalizeMut import (
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
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadValidateMut import (
    ReadValidMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadValueMut import ReadValueMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadVirtualMut import (
    ReadVirtualMut,
)

# shared field handlers keep native owner registries declarative as the graph grammar grows
KReadActions: MappingProxyType[str, Callable[[ReadFrame, NativeField], None]] = (
    MappingProxyType(
        {
            "Scalar": ReadValueMut,
            "Text": ReadValueMut,
            "Node": ReadValueMut,
            "Base": ReadNestedMut,
            "Embed": ReadNestedMut,
            "Array": ReadArrayMut,
            "Boolean": ReadBooleanMut,
            "Present": ReadPresentMut,
            "Branch": ReadBranchMut,
            "Context": ReadControlMut,
            "Mask": ReadControlMut,
            "Virtual": ReadVirtualMut,
            "Validate": ReadValidMut,
            "Section": ReadSectionMut,
            "Direct": ReadDirectMut,
            "Bytes": ReadBytesMut,
            "Length": ReadLengthMut,
            "Repeat": ReadRepeatMut,
            "Normalize": ReadNormalMut,
            "GhostCount": ReadGhostMut,
            "MassCaches": ReadMassMut,
            "BBoxCache": ReadBBoxMut,
            "DirectNode": ReadOwnedMut,
            "Packed": ReadPackedMut,
        }
    )
)
