from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation

from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineAxis import (
    LineAxis,
)
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)


# unary axis rules refer to their actual indexed line rather than an inferred rectangle side
def LineAxisRule(
    ProfileId: int,
    AxisValue: LineAxis,
    EntityIds: tuple[str, ...],
    LineIndices: tuple[int, ...],
) -> SketchRelation:
    NativeId = f"{ProfileId}:log_g1:{AxisValue.IndexValue}"
    return SketchRelation(
        id=f"sldprt:constraint:{NativeId}",
        kind="horizontal" if AxisValue.CodeValue == 4 else "vertical",
        references=(ConstraintRef(EntityIds[LineIndices.index(AxisValue.LineValue)]),),
        provenance=TypedProvenance(AxisValue.OwnerValue, NativeId),
        attributes=FreezeMapping(
            {
                "native_code": AxisValue.CodeValue,
                "native_line_index": AxisValue.LineValue,
                "native_handle_index": AxisValue.HandleValue.IndexValue,
                "typed_archive_owner": AxisValue.OwnerValue,
            }
        ),
    )
