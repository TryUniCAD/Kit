from convert.Geometry.Extrude.Circular.CircularExtrude import BuildCircular
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.Partition.PartMass import PartMass
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CircleSolid import (
    CircleSolid,
)
from interchange.Records.RecordTopology import TopologyCounts
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector


# checked circular ownership supplies the analytic body without inventing saved kernel geometry
def ColdCircle(ModelValue: NativeModel, BodyId: str) -> CircleSolid | None:
    if len(ModelValue.sketches) != 1 or len(ModelValue.operations) != 1:
        return None
    (SketchValue,) = ModelValue.sketches
    (Operation,) = ModelValue.operations
    CircleValue, FrameValue = SketchValue.TypedCircle, SketchValue.TypedFrame
    DepthValue = Operation.length_mm
    if CircleValue is None or FrameValue is None or DepthValue is None:
        return None
    RadiusValue = CircleValue.RadiusValue
    Profile = CircleGeometry(PlaneVector(*CircleValue.CenterValue), RadiusValue)
    Lower, Upper = (-DepthValue, 0.0) if Operation.direction_code else (0.0, DepthValue)
    try:
        BodyValue, Volume, AreaValue, Bounds = BuildCircular(
            BodyId, FrameValue, Profile, Lower, Upper, RadiusValue, RadiusValue
        )
    except (ValueError, OverflowError):
        return None
    if BodyValue.validate(frozenset((BodyId,))):
        return None
    Center = (Lower + Upper) / 2.0
    Centroid = (
        FrameValue.origin.x
        + Profile.center.x * FrameValue.x_axis.x
        + Profile.center.y * FrameValue.y_axis.x
        + Center * FrameValue.z_axis.x,
        FrameValue.origin.y
        + Profile.center.x * FrameValue.x_axis.y
        + Profile.center.y * FrameValue.y_axis.y
        + Center * FrameValue.z_axis.y,
        FrameValue.origin.z
        + Profile.center.x * FrameValue.x_axis.z
        + Profile.center.y * FrameValue.y_axis.z
        + Center * FrameValue.z_axis.z,
    )
    return CircleSolid(
        BodyValue,
        TopologyCounts(
            solid_count=1,
            shell_count=len(BodyValue.shells),
            face_count=len(BodyValue.faces),
            edge_count=len(BodyValue.edges),
            vertex_count=len(BodyValue.vertices),
            bounding_box=Bounds,
            volume=Volume,
            surface_area=AreaValue,
            valid=True,
        ),
        PartMass(Volume, Centroid),
    )
