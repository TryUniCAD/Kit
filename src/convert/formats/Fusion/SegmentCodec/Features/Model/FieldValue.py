from typing import TypeAlias

from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.formats.Fusion.SegmentCodec.Features.Model.VectorValue import VectorValue

KFieldValue: TypeAlias = (
    bool
    | int
    | float
    | str
    | LocalRef
    | VectorValue
    | tuple[LocalRef | None, ...]
    | None
)
