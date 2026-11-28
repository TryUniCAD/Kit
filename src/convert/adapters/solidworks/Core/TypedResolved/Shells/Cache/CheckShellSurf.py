from collections.abc import Mapping
from math import isclose as IsClose

from convert.Geometry.Revolve.SweepVector import DotVector, OffsetVector
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.VectorSpace import SpaceVector


# every actual planar carrier must contain all corners of its saved trim
def CheckShellSurf(
    ModelValue: BrepModel,
    RingByLoop: Mapping[str, tuple[SpaceVector, ...]],
    BoundValue: float,
) -> None:
    Surfaces = {Value.id: Value for Value in ModelValue.surfaces}
    if set(Surfaces) != {Value.surface_id for Value in ModelValue.faces}:
        raise ValueError("SOLIDWORKS shell has unrelated saved surface carriers")
    for FaceValue in ModelValue.faces:
        Surface = Surfaces[FaceValue.surface_id]
        if (
            not isinstance(Surface, PlaneSurface)
            or not IsClose(
                DotVector(Surface.normal, Surface.normal),
                1.0,
                abs_tol=0.0,
                rel_tol=1e-14,
            )
            or any(
                abs(
                    DotVector(
                        Surface.normal, OffsetVector(PointValue, Surface.origin, -1.0)
                    )
                )
                > BoundValue
                for LoopId in FaceValue.loop_ids
                for PointValue in RingByLoop[LoopId]
            )
        ):
            raise ValueError("SOLIDWORKS shell has a plane outside its actual trim")
