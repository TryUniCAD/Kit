from pathlib import Path
from typing import cast as CastValue

from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from tests.Convert.Integration.Fusion.DualSide.DualCase import DualCase


# actual api frames separate profile coordinates from measured world placement
def ReadDualCase(
    Source: Path, Digest: str, Identity: str, Reading: dict[str, object]
) -> DualCase:
    Profile = CastValue(dict[str, object], Reading["profile"])
    Matrix = CastValue(list[float], Profile["transform"])
    WorldCenter = CastValue(list[float], Profile["center_world_cm"])
    Frame = Transform(
        SpaceVector(*(Matrix[Index] * 10 for Index in (3, 7, 11))),
        SpaceVector(*(Matrix[Index] for Index in (0, 4, 8))),
        SpaceVector(*(Matrix[Index] for Index in (1, 5, 9))),
        SpaceVector(*(Matrix[Index] for Index in (2, 6, 10))),
    )
    LocalCenter = tuple(
        sum(
            (WorldCenter[Index] * 10 - Matrix[3 + Index * 4] * 10)
            * Matrix[Index * 4 + Column]
            for Index in range(3)
        )
        for Column in range(2)
    )
    return DualCase(
        Source,
        Digest,
        Identity,
        CircleGeometry(
            PlaneVector(*LocalCenter), CastValue(float, Profile["radius_cm"]) * 10
        ),
        Frame,
        CastValue(float, Reading["first"]) * 10,
        CastValue(float, Reading["second"]) * 10,
        CastValue(float, Reading["draft_first"]),
        CastValue(float, Reading["draft_second"]),
        Reading,
    )
