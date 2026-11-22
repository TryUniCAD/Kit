from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation

from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.DriverLine import (
    DriverLine,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineDriver import (
    LineDriver,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineParamId import (
    LineParamId,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)


# point distances retain both selected subelements and their actual named driving parameter
def LineValueRule(
    ProfileId: int,
    DriverValue: LineDriver,
    LoopValue: LineLoop,
    EntityIds: tuple[str, ...],
) -> SketchRelation:
    LineValue = DriverLine(DriverValue, LoopValue)
    NativeId = f"{ProfileId}:dimension:{DriverValue.NodeValue.FieldsValue['f50']}"
    return SketchRelation(
        id=f"sldprt:constraint:{NativeId}",
        kind="distance",
        references=tuple(
            ConstraintRef(
                EntityIds[LineValue.IndexValue],
                "start" if Index == LineValue.StartValue else "end",
            )
            for Index in DriverValue.PointValues
        ),
        parameter_id=LineParamId(ProfileId, DriverValue.NameValue),
        provenance=TypedProvenance(DriverValue.OwnerValue, NativeId),
        attributes=FreezeMapping(
            {
                "native_code": 1,
                "native_dimension_id": DriverValue.NodeValue.FieldsValue["f50"],
                "native_point_indices": DriverValue.PointValues,
                "native_display_index": DriverValue.DisplayValue.IndexValue,
                "native_handle_index": DriverValue.HandleValue.IndexValue,
                "native_parameter_owner": DriverValue.ParamOwner,
                "native_display_text_point_m": DriverValue.TextPosition,
                "native_display_selected_leader": DriverValue.SelectedLeader,
                "native_display_route_center": DriverValue.RouteCenter,
                "native_display_design_intent": DriverValue.DesignIntent,
                "typed_archive_owner": DriverValue.OwnerValue,
            }
        ),
    )
