from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.LineEqual import (
    LineEqual,
)
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation


# the neutral equal length constraint preserves the actual ordered local operands and embedded native ownership
def MakeRevEqual(
    ProfileId: int, EqualValue: LineEqual, EntityIds: dict[int, str]
) -> SketchRelation:
    NativeId = f"{ProfileId}:log_g2:0"
    return SketchRelation(
        id=f"sldprt:constraint:{NativeId}",
        kind="equal",
        references=tuple(
            ConstraintRef(EntityIds[IndexValue]) for IndexValue in EqualValue.Indices
        ),
        provenance=TypedProvenance(EqualValue.OwnerValue, NativeId),
        attributes=FreezeMapping(
            {
                "native_code": 14,
                "native_line_indices": EqualValue.Indices,
                "typed_archive_owner": EqualValue.OwnerValue,
            }
        ),
    )
