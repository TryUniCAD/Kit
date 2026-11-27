from math import tau as FullTurn
from typing import cast as CastValue

from convert.Geometry.Extrude.Circular.DualSide.DualFrame import DualFrame
from convert.Geometry.Extrude.Circular.DualSide.DualMeasure import DualMeasure
from convert.Geometry.Extrude.Circular.DualSide.DualMeridian import DualMeridian
from convert.Geometry.Revolve.FullFaces import BuildFullFaces
from convert.Geometry.Revolve.FullRings import BuildFullRings
from convert.Geometry.Revolve.SweepBounds import GetSweepBounds
from convert.Geometry.Revolve.SweepModel import BuildSweepModel
from convert.Geometry.Revolve.SweepVector import OffsetVector
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


# independently drafted sides share one rim while retaining exact closed solid topology
def BuildDualSide(
    BodyId: str,
    FrameValue: Transform,
    Profile: CircleGeometry,
    FirstMm: float,
    SecondMm: float,
    FirstTaper: float,
    SecondTaper: float,
) -> tuple[BrepModel, float, float, SpaceVector, BoundingBox]:
    if not isinstance(CastValue(object, BodyId), str) or not BodyId.strip():
        raise ValueError("Circular sides require a design body identity")
    Frame = DualFrame(FrameValue, Profile)
    Meridian = DualMeridian(Profile.radius, FirstMm, SecondMm, FirstTaper, SecondTaper)
    try:
        Volume, AreaValue, Center = DualMeasure(Meridian)
    except (OverflowError, ZeroDivisionError) as ErrorValue:
        raise ValueError(
            "Circular side measures exceed finite geometry"
        ) from ErrorValue
    Bounds = GetSweepBounds(
        Meridian, Frame.origin, Frame.z_axis, Frame.x_axis, 0.0, FullTurn
    )
    Prefix = f"{BodyId}-sides"
    Vertices, Curves, Rings = BuildFullRings(Prefix, Meridian, Frame)
    Surfaces, Faces, Loops, Coedges = BuildFullFaces(Prefix, Meridian, Frame, Rings)
    Geometry = BuildSweepModel(
        BodyId,
        Prefix,
        Curves,
        Surfaces,
        Vertices,
        tuple(Rings.values()),
        Faces,
        Loops,
        Coedges,
    )
    return (
        Geometry,
        Volume,
        AreaValue,
        OffsetVector(Frame.origin, Frame.z_axis, Center),
        Bounds,
    )
