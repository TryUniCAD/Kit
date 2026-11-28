from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.RequirePolygon import (
    RequirePolygon,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.ThruOwnerInput import (
    ThruOwnerInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.OwnerBind import (
    OwnerBind,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    ReadRows,
    RequireRecord,
)


# each source edge and relation needs the actual generated record selected by geometric correspondence rather than recorded source indexes
def MapThruLines(
    InputValue: ThruOwnerInput, ProfileValue: ProfileGraph
) -> tuple[OwnerBind, ...]:
    Geometry = RequirePolygon(ProfileValue.GeometryValue)
    DimsValue = RequireRecord(Geometry.SketchValue.FieldsValue["dims"])
    LogicalValues = ReadRows(DimsValue["log_g1"])
    if len(LogicalValues) != 4:
        raise ValueError("generated source stock lost its four actual relations")
    if any(
        type(CastValue(object, Value.IsReversed)) is not bool
        or Value.AxisKind
        != ("horizontal" if Value.TargetIndex % 2 == 0 else "vertical")
        for Value in InputValue.LineValues
    ):
        raise ValueError("source line orientation or axis relation is unsupported")
    return tuple(
        Binding
        for LineValue in InputValue.LineValues
        for Binding in (
            OwnerBind(
                LineValue.EntityId,
                "line_reversed" if LineValue.IsReversed else "line",
                Geometry.SketchValue,
                Geometry.LineValues[LineValue.TargetIndex],
            ),
            OwnerBind(
                LineValue.RelationId,
                "unary_axis",
                Geometry.SketchValue,
                RequireRecord(LogicalValues[LineValue.TargetIndex]["d"]),
            ),
        )
    )
