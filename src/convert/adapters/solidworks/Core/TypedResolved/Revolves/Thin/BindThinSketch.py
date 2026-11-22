from dataclasses import replace as ReplaceValue

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


# an open body line and its distinct actual axis replace only the captured thin profile geometry
def BindThinSketch(SketchValue: Sketch, SweepValue: RevolveOwner) -> Sketch:
    ShapeValue = SweepValue.ProfileGraph
    LoopValue = ShapeValue.LoopValue
    ProfileId = NativeNodeId(SweepValue.ProfileValue)
    (BodyValue,) = LoopValue.LinesValue
    AxisLoop = ReplaceValue(
        LoopValue,
        PointsValue=(*LoopValue.PointsValue, *ShapeValue.AxisPoints.values()),
        LinesValue=(ShapeValue.AxisValue,),
        OrderValue=(),
    )
    AxisValue = ReplaceValue(
        LineEntity(ProfileId, AxisLoop, ShapeValue.AxisValue), construction=True
    )
    return ReplaceValue(
        SketchValue,
        entities=(LineEntity(ProfileId, LoopValue, BodyValue), AxisValue),
        constraints=(),
        parameter_ids=(),
        closed_profile_entity_ids=(),
        provenance=TypedProvenance(LoopValue.OwnerValue, str(ProfileId)),
        attributes=FreezeMapping(
            {
                **SketchValue.attributes,
                "typed_thin_revolve_profile": True,
                "native_point_rows": MakeRevPoints(ShapeValue),
                "native_axis_array_index": ShapeValue.AxisValue.IndexValue,
                "native_axis_permanent_mark": ShapeValue.AxisValue.PermanentId,
                "typed_archive_owner": LoopValue.OwnerValue,
            }
        ),
    )
