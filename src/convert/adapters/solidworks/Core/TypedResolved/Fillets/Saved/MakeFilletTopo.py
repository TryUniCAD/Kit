from math import pi as PiValue

from interchange.Records.RecordTopology import TopologyCounts
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.VectorSpace import SpaceVector


# the confirmed quarter cylinder removes an exact corner sector from the prior box
def MakeFilletTopo(
    Bounds: tuple[tuple[float, float], ...],
    AxisIndex: int,
    Radius: float,
) -> TopologyCounts:
    Sizes = tuple((Upper - Lower) * 1000.0 for Lower, Upper in Bounds)
    Length = Sizes[AxisIndex]
    RadiusMm = Radius * 1000.0
    Width, Height, Depth = Sizes
    Removed = (1.0 - PiValue / 4) * RadiusMm * RadiusMm
    AreaValue = 2 * (Width * Height + Width * Depth + Height * Depth)
    return TopologyCounts(
        solid_count=1,
        shell_count=1,
        face_count=7,
        edge_count=15,
        vertex_count=10,
        bounding_box=BoundingBox(
            SpaceVector(*(Lower * 1000.0 for Lower, _ in Bounds)),
            SpaceVector(*(Upper * 1000.0 for _, Upper in Bounds)),
        ),
        volume=Width * Height * Depth - Removed * Length,
        surface_area=AreaValue - 2 * Removed + (PiValue / 2 - 2) * RadiusMm * Length,
        valid=True,
    )
