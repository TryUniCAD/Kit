from collections.abc import Mapping

from convert.Geometry.Revolve.SweepVector import CrossVector, DotVector, OffsetVector
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    KPrismResidual,
)
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.VectorSpace import SpaceVector


# saved faces can use reversed carriers while their shell rings still follow the outward boundary
def CheckEqPlanes(
    Actual: BrepModel,
    Planes: Mapping[str, PlaneSurface],
    Rings: tuple[tuple[SpaceVector, ...], ...],
) -> None:
    Faces = {FaceValue.id: FaceValue for FaceValue in Actual.faces}
    if (
        Actual.shell_uses[0].reversed
        or any(UseValue.reversed for UseValue in Actual.face_uses)
        or any(not LoopValue.outer for LoopValue in Actual.loops)
        or any(len(FaceValue.loop_ids) != 1 for FaceValue in Actual.faces)
    ):
        raise ValueError("saved width-depth body requires one outward ring per face")
    for UseValue, RingValue in zip(Actual.face_uses, Rings, strict=True):
        FaceValue = Faces[UseValue.face_id]
        Plane = Planes[FaceValue.surface_id]
        First, Second, Third, _ = RingValue
        Normal = CrossVector(
            OffsetVector(Second, First, -1.0), OffsetVector(Third, First, -1.0)
        )
        Sense = 1 if FaceValue.same_sense else -1
        if not Sense * DotVector(Normal, Plane.normal) > 0.0 or any(
            not abs(DotVector(OffsetVector(Point, Plane.origin, -1.0), Plane.normal))
            <= KPrismResidual
            for Point in RingValue
        ):
            raise ValueError("saved width-depth face conflicts with its plane carrier")
