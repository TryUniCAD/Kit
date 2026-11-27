from convert.adapters.Fusion.Native.Circular.DualSides.CheckDualMass import (
    CheckDualMass,
)
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphValues import TextValue
from convert.Geometry.Extrude.Circular.DualSide.BuildDualSide import BuildDualSide
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Features.DistanceValues import DistExtValues
from interchange.Features.FeatureBody import DesignBody
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Transform import KTransformIdentity, Transform
from interchange.Records.RecordTopology import TopologyCounts


# the public body retains exact topology and measures from both independent sides
def ProjectDualBody(
    Context: ExtrudeContext,
    Profile: CircleGeometry,
    Values: DistExtValues,
    MaterialId: str,
    FrameValue: Transform = KTransformIdentity,
) -> tuple[BrepModel, DesignBody]:
    if Values.SecondTaperRadians is None or Values.OffsetMm != 0:
        raise ValueError("Native circular draft sides require a profile plane start")
    Geometry, Volume, AreaValue, Center, Bounds = BuildDualSide(
        Context.BodyNode.Identity,
        FrameValue,
        Profile,
        Values.UpperMm,
        -Values.LowerMm,
        Values.TaperRadians,
        Values.SecondTaperRadians,
    )
    CheckDualMass(Context, Profile, Values, Volume, AreaValue, Center, FrameValue)
    Counts = TopologyCounts(
        1,
        len(Geometry.shells),
        len(Geometry.faces),
        len(Geometry.edges),
        len(Geometry.vertices),
        Volume,
        AreaValue,
        Bounds,
        True,
    )
    BodyValue = DesignBody(
        Context.BodyNode.Identity,
        TextValue(Context.BodyNode.Fields["userName"]),
        Context.Extrude.Identity,
        Counts,
        MaterialId,
        attributes={"creation_index": Context.BodyNode.Fields["creationIndex"]},
    )
    return Geometry, BodyValue
