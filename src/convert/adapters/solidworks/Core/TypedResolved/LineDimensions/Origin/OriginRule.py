from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation

from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.Origin.LineOrigin import (
    LineOrigin,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.Origin.OriginMetadata import (
    OriginMetadata,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.Origin.OriginPointId import (
    OriginPointId,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)


# coincidence references must select the actual fixed external datum and an actual incident contour endpoint
def OriginRule(
    ProfileId: int,
    OriginValue: LineOrigin,
    LoopValue: LineLoop,
    EntityIds: tuple[str, ...],
) -> SketchRelation:
    Matches = tuple(
        (
            LineValue.IndexValue,
            "start" if LineValue.StartValue == OriginValue.LocalIndex else "end",
        )
        for LineValue in LoopValue.LinesValue
        if OriginValue.LocalIndex in (LineValue.StartValue, LineValue.EndValue)
    )
    if len(Matches) != 2:
        raise ValueError("origin coincidence corner lacks its two real contour edges")
    LineIndex, PointName = min(Matches)
    EntityIndex = next(
        Index
        for Index, LineValue in enumerate(LoopValue.LinesValue)
        if LineValue.IndexValue == LineIndex
    )
    NativeId = f"{ProfileId}:log_g2:0"
    return SketchRelation(
        id=f"sldprt:constraint:{NativeId}",
        kind="coincident",
        references=(
            ConstraintRef(OriginPointId(ProfileId, OriginValue)),
            ConstraintRef(EntityIds[EntityIndex], PointName),
        ),
        provenance=TypedProvenance(OriginValue.OwnerValue, NativeId),
        attributes=FreezeMapping(
            {
                **OriginMetadata(OriginValue),
                "native_code": 9,
                "native_point_indices": (
                    OriginValue.ExternalIndex,
                    OriginValue.LocalIndex,
                ),
                "native_relation_fields": {
                    NameValue: Value
                    for NameValue, Value in OriginValue.RelationValue.items()
                    if NameValue not in ("h1", "h2")
                },
            }
        ),
    )
