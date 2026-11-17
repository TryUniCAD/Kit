from math import cos as CosValue, pi as KPiValue, sin as SinValue

from tests.Convert.Solidworks.Research.FreshPartInput import MakePartInput


# independent regular polygon inputs vary topology and depth without any native fixture supplying fields
def BlindPartInput(VertexCount: int, DepthValue: float) -> dict[str, object]:
    PointsValue = [
        [
            0.023 * CosValue(2 * KPiValue * Index / VertexCount),
            0.023 * SinValue(2 * KPiValue * Index / VertexCount),
        ]
        for Index in range(VertexCount)
    ]
    return MakePartInput(PointsValue, DepthValue, "SdkConstructedBlindBoss")
