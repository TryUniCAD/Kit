from typing import cast as CastValue

from convert.Geometry.Fillet.Circular.RimMoments import RimMoments
from convert.Geometry.Revolve.FullFaces import BuildFullFaces
from convert.Geometry.Revolve.FullRings import BuildFullRings
from convert.Geometry.Revolve.SweepModel import BuildSweepModel
from interchange.brep.Surfaces.BrepSurfaces import TorusSurface
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


# circular junctions bound the exact quarter torus while preserving negative x seam vertices
def BuildRimFillet(
    BodyId: str, Radius: float, Height: float, Fillet: float
) -> tuple[BrepModel, float, float, SpaceVector, BoundingBox]:
    if not isinstance(CastValue(object, BodyId), str) or not BodyId.strip():
        raise ValueError("Circular rim requires a design body identity")
    Volume, AreaValue, Center, _, _ = RimMoments(Radius, Height, Fillet)
    Meridian = (
        (0.0, 0.0),
        (Radius, 0.0),
        (Radius, Height - Fillet),
        (Radius - Fillet, Height),
        (0.0, Height),
    )
    Frame = Transform(
        x_axis=SpaceVector(-1.0, 0.0, 0.0),
        y_axis=SpaceVector(0.0, -1.0, 0.0),
    )
    Prefix = f"{BodyId}-rim"
    Vertices, Curves, Edges = BuildFullRings(Prefix, Meridian, Frame)
    Surfaces, Faces, Loops, Coedges = BuildFullFaces(Prefix, Meridian, Frame, Edges)
    Rounded = TorusSurface(
        Surfaces[2].id,
        SpaceVector(0.0, 0.0, Height - Fillet),
        SpaceVector(0.0, 0.0, 1.0),
        SpaceVector(1.0, 0.0, 0.0),
        Radius - Fillet,
        Fillet,
    )
    Geometry = BuildSweepModel(
        BodyId,
        Prefix,
        Curves,
        (*Surfaces[:2], Rounded, Surfaces[3]),
        Vertices,
        tuple(Edges.values()),
        Faces,
        Loops,
        Coedges,
    )
    return (
        Geometry,
        Volume,
        AreaValue,
        SpaceVector(0.0, 0.0, Center),
        BoundingBox(
            SpaceVector(-Radius, -Radius, 0.0), SpaceVector(Radius, Radius, Height)
        ),
    )
