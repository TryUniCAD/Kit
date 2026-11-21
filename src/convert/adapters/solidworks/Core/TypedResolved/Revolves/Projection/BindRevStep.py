from dataclasses import replace as ReplaceValue
from math import degrees as Degrees

from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection


# normalized angular intent must retain its positive owned parameter and explicit selected axis through public validation
def BindRevStep(
    StepValue: FeatureStep,
    OwnerValue: RevolveOwner,
    LinkValue: NativeLink,
    SelectValue: Selection,
    ParamIds: tuple[str, ...],
    Operation: BooleanOp = BooleanOp.KJoin,
    StockId: str | None = None,
) -> FeatureStep:
    NativeId = NativeNodeId(OwnerValue.NodeValue)
    ProfileId = NativeNodeId(OwnerValue.ProfileValue)
    if StepValue.id != f"sldprt:feature:{NativeId}":
        raise ValueError(
            "ordinary revolve neutral feature does not alias its actual owner"
        )
    FrameValue = OwnerValue.FrameValue
    return ReplaceValue(
        StepValue,
        kind=FeatureKind.KRevolution,
        input_feature_ids=(f"sldprt:feature:{ProfileId}",)
        + ((StockId,) if StockId is not None else ()),
        sketch_id=f"sldprt:sketch:{ProfileId}",
        parameter_ids=ParamIds,
        selection_ids=(SelectValue.id,),
        operation=Operation,
        definition=AngularRevolve(
            SelectValue.id,
            ParamIds[0],
            FrameValue.StartValue,
            FrameValue.DirectionValue,
            SideMode=OwnerValue.EndValue.ModeValue,
            AgainstParameterId=ParamIds[1] if len(ParamIds) == 2 else None,
        ),
        provenance=TypedProvenance(
            NativeNodeSpan(LinkValue, OwnerValue.NodeValue), str(NativeId)
        ),
        attributes=FreezeMapping(
            {
                **StepValue.attributes,
                "typed_revolve_semantics": True,
                "native_reverse_direction": OwnerValue.IsReverse,
                "direction_code": int(OwnerValue.IsReverse),
                "angle_degrees": Degrees(OwnerValue.AngleValue.RadiansValue),
                "axis_source_kind": "sketch",
                "axis_source_id": ProfileId,
                "native_axis_permanent_mark": OwnerValue.ProfileGraph.AxisValue.PermanentId,
                "typed_archive_owner": NativeNodeSpan(LinkValue, OwnerValue.NodeValue),
            }
        ),
    )
