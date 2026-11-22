from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineAxisRule import (
    LineAxisRule,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineEntity import LineEntity
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.MakeRevPoints import (
    MakeRevPoints,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Sketch import Sketch


# exact contour entities and actual unary relations must replace inferred endpoints without anchoring the selected axis
def MakeRevSketch(SketchValue: Sketch, OwnerValue: RevolveOwner) -> Sketch:
    GraphValue = OwnerValue.ProfileGraph
    LoopValue = GraphValue.LoopValue
    ProfileId = NativeNodeId(OwnerValue.ProfileValue)
    if SketchValue.id != f"sldprt:sketch:{ProfileId}":
        raise ValueError(
            "ordinary revolve neutral sketch identity differs from its actual profile"
        )
    Entities = tuple(
        LineEntity(ProfileId, LoopValue, LineValue)
        for LineValue in LoopValue.LinesValue
    )
    AxisLoop = ReplaceValue(
        LoopValue,
        PointsValue=(*LoopValue.PointsValue, *GraphValue.AxisPoints.values()),
        LinesValue=(GraphValue.AxisValue,),
        OrderValue=(),
    )
    AxisEntity = ReplaceValue(
        LineEntity(ProfileId, AxisLoop, GraphValue.AxisValue), construction=True
    )
    RulesValue = tuple(
        LineAxisRule(
            ProfileId,
            RuleValue,
            tuple(Entity.id for Entity in Entities),
            tuple(LineValue.IndexValue for LineValue in LoopValue.LinesValue),
        )
        for RuleValue in GraphValue.AxisRules
    )
    return ReplaceValue(
        SketchValue,
        entities=(*Entities, AxisEntity),
        constraints=RulesValue,
        parameter_ids=(),
        closed_profile_entity_ids=(
            tuple(Entities[IndexValue].id for IndexValue in LoopValue.OrderValue),
        ),
        provenance=TypedProvenance(LoopValue.OwnerValue, str(ProfileId)),
        attributes=FreezeMapping(
            {
                **SketchValue.attributes,
                "typed_revolve_profile": True,
                "native_profile_count": 1,
                "typed_archive_owner": LoopValue.OwnerValue,
                "native_point_rows": MakeRevPoints(GraphValue),
                "native_line_regions": GraphValue.RegionValues,
                "native_axis_array_index": GraphValue.AxisValue.IndexValue,
                "native_axis_permanent_mark": GraphValue.AxisValue.PermanentId,
                "axis_solver_relations": (),
                "native_solver_status_measured": False,
            }
        ),
    )
