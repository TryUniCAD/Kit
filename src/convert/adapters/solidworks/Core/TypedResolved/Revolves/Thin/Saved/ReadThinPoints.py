from math import hypot as Hypot

from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.VectorSpace import SpaceVector


# the small millimetre tolerance is the existing native kernel point comparison bound
def IsPointNear(Actual: SpaceVector, Expected: SpaceVector) -> bool:
    return (
        Hypot(Actual.x - Expected.x, Actual.y - Expected.y, Actual.z - Expected.z)
        <= 1e-9
    )


# every trimmed sector corner must identify one unique physical cache vertex
def ReadThinPoints(Actual: BrepModel, Expected: BrepModel) -> dict[str, str]:
    PointsValue: dict[str, str] = {}
    for VertexValue in Actual.vertices:
        Matches = tuple(
            Target.id
            for Target in Expected.vertices
            if IsPointNear(VertexValue.point, Target.point)
        )
        if len(Matches) != 1:
            raise ValueError(
                "SOLIDWORKS thin cache has a vertex outside the editable sector"
            )
        PointsValue[VertexValue.id] = Matches[0]
    if len(PointsValue) != len(Expected.vertices) or len(
        set(PointsValue.values())
    ) != len(PointsValue):
        raise ValueError(
            "SOLIDWORKS thin cache does not own every editable sector corner"
        )
    return PointsValue
