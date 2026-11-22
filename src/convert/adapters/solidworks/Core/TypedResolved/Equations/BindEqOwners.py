from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Native import NativeModel, NativeProfile
from convert.adapters.solidworks.Core.TypedResolved.BindExtrude import (
    BindDepth,
    BindExtrude,
)
from convert.adapters.solidworks.Core.TypedResolved.Equations.CheckEqBoss import (
    CheckEqBoss,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Equations.ReadEqLoop import (
    ReadEqLoop,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineNativeDims import (
    LineNativeDims,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# sketch and boss dimensions must attach to the same actual feature owners used by the equation
def BindEqOwners(
    Model: NativeModel, LinkValue: NativeLink
) -> tuple[NativeModel, ExtrudeOwner]:
    (Sketch,) = Model.sketches
    (Operation,) = Model.operations
    Features = IndexFeatures(LinkValue)
    Profile = RequireNative(Features[Sketch.object_id], "moProfileFeature_c")
    BossValue = ReadExtrude(LinkValue, Features[Operation.object_id], Features)
    CheckEqBoss(BossValue)
    if BossValue.ProfileValue is not Profile:
        raise ValueError("local equation boss does not select its actual sketch")
    FrameValue = ReadPrismFrame(Profile, LinkValue.ConfigValue.RootValue, Features)
    Reference = RequireNative(Profile.FieldsValue.get("pd_f78"), "moCompRefPlane_c")
    PlaneId = NativeRecord(Reference.FieldsValue.get("ff0")).get("f00")
    if type(PlaneId) is not int or not any(
        Plane.object_id == PlaneId for Plane in Model.planes
    ):
        raise ValueError("local equation has no resolved Front support")
    LoopValue = ReadEqLoop(Profile, LinkValue)
    Dimensions = LineNativeDims(LoopValue.DimsValue)
    Contour = NativeProfile(
        "line-loop",
        tuple(
            Coordinate
            for Point in LoopValue.PointsValue
            for Coordinate in Point.PositionValue
        ),
        (),
    )
    ModelValue = ReplaceValue(
        Model,
        sketches=(
            ReplaceValue(
                Sketch,
                support_plane_id=PlaneId,
                TypedFrame=FrameValue,
                TypedLines=LoopValue,
                profiles=(Contour,),
                dimensions=Dimensions,
                constraints=(),
            ),
        ),
        operations=(BindExtrude(Operation, BossValue),),
        features=tuple(
            (
                BindDepth(Feature, BossValue)
                if Feature.object_id == Operation.object_id
                else (
                    ReplaceValue(Feature, dimensions=Dimensions)
                    if Feature.object_id == Sketch.object_id
                    else Feature
                )
            )
            for Feature in Model.features
        ),
    )
    return ModelValue, BossValue
