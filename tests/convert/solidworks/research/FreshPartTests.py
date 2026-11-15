from __future__ import annotations

from math import cos as CosAngle, pi as PiValue, sin as SinAngle
from typing import cast as CastValue

from tests.convert.solidworks.research.FreshPartInput import MakePartInput
from tests.convert.solidworks.research.FreshPartRunner import RunFreshPart


def AssertPart(Report: dict[str, object], PointCount: int, DepthValue: float) -> None:
    Streams = CastValue(dict[str, dict[str, object]], Report["streams"])
    assert len(Streams) == 8
    assert all(Result["passed"] for Result in Streams.values()), Streams
    assert all(Result["tail"] == 0 for Result in Streams.values())
    assert Report["points"] == Report["lines"] == PointCount
    assert Report["depth"] == DepthValue
    assert Report["denied_reads"] == []
    assert Report["module_reads"]
    assert Report["vendor_acceptance"] == "unverified"
    Linked = Streams["Contents/Config-0-ResolvedFeatures"]
    assert Linked["seeded_map_count"] == Linked["map_base"] == Report["map_count"]


def TestFreshParts() -> None:
    Triangle = [[0.0, 0.0], [0.04, 0.0], [0.005, 0.03]]
    RingPoints = [
        [0.02 * CosAngle(Index * PiValue / 32), 0.02 * SinAngle(Index * PiValue / 32)]
        for Index in range(64)
    ]
    First = RunFreshPart(MakePartInput(Triangle, 0.0123, "authored triangle"))
    Second = RunFreshPart(MakePartInput(RingPoints, 0.0197, "authored ring"))
    AssertPart(First, 3, 0.0123)
    AssertPart(Second, 64, 0.0197)
    SmallSizes = CastValue(dict[str, int], First["sizes"])
    LargeSizes = CastValue(dict[str, int], Second["sizes"])
    assert (
        LargeSizes["Contents/Config-0-ResolvedFeatures"]
        > SmallSizes["Contents/Config-0-ResolvedFeatures"]
    )
    assert First["features"] == Second["features"]
    assert First["next_id"] == Second["next_id"]
