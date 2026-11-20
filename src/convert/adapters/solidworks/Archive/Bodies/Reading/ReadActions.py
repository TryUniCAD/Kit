from collections.abc import Callable
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadArrayMut import ReadArrayMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadNestedMut import (
    ReadNestedMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadPresentMut import (
    ReadPresentMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadValueMut import ReadValueMut

# field dispatch admits only the operations with shared body implementations
KReadActions: MappingProxyType[str, Callable[[ReadFrame, NativeField], None]] = (
    MappingProxyType(
        {
            "Scalar": ReadValueMut,
            "Text": ReadValueMut,
            "Node": ReadValueMut,
            "Base": ReadNestedMut,
            "Embed": ReadNestedMut,
            "Array": ReadArrayMut,
            "Present": ReadPresentMut,
        }
    )
)
