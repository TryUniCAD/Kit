from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.BuildShape import (
    BuildShape,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.CapFace import CapFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LoopMath import (
    LoopArea,
    LoopPolygon,
    SpanArea,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import SpanLength


def PlaneMoments(Polygon: list[tuple[float, float]]) -> dict[str, float]:
    SumValues = dict(x=0.0, y=0.0, xx=0.0, yy=0.0, xy=0.0)
    for Index, (StartX, StartY) in enumerate(Polygon):
        FinishX, FinishY = Polygon[(Index + 1) % len(Polygon)]
        Cross = StartX * FinishY - FinishX * StartY
        SumValues["x"] += (StartX + FinishX) * Cross / 6.0
        SumValues["y"] += (StartY + FinishY) * Cross / 6.0
        SumValues["xx"] += (
            (StartX * StartX + StartX * FinishX + FinishX * FinishX) * Cross / 12.0
        )
        SumValues["yy"] += (
            (StartY * StartY + StartY * FinishY + FinishY * FinishY) * Cross / 12.0
        )
        SumValues["xy"] += (
            (
                StartX * FinishY
                + 2 * StartX * StartY
                + 2 * FinishX * FinishY
                + FinishX * StartY
            )
            * Cross
            / 24.0
        )
    return SumValues


def SolidMass(Solid: PrismSolid) -> dict[str, float]:
    MassValue = dict(
        volume=0.0, x=0.0, y=0.0, z=0.0, xx=0.0, yy=0.0, zz=0.0, xy=0.0, xz=0.0, yz=0.0
    )
    for SlabValue in Solid.Slabs:
        Lower, Upper = SlabValue.LowerCm, SlabValue.UpperCm
        Height = Upper - Lower
        AreaValue = sum(LoopArea(LoopValue) for LoopValue in SlabValue.Loops)
        Plane = dict(x=0.0, y=0.0, xx=0.0, yy=0.0, xy=0.0)
        for LoopValue in SlabValue.Loops:
            for KeyValue, Value in PlaneMoments(LoopPolygon(LoopValue, 4096)).items():
                Plane[KeyValue] += Value
        Linear, Square = (Upper * Upper - Lower * Lower) / 2.0, (
            Upper**3 - Lower**3
        ) / 3.0
        MassValue["volume"] += AreaValue * Height
        MassValue["z"] += AreaValue * Linear
        MassValue["zz"] += AreaValue * Square
        MassValue["xz"] += Plane["x"] * Linear
        MassValue["yz"] += Plane["y"] * Linear
        for KeyValue in ("x", "y", "xx", "yy", "xy"):
            MassValue[KeyValue] += Plane[KeyValue] * Height
    MassValue["area"] = SolidArea(Solid)
    return MassValue


def SolidArea(Solid: PrismSolid) -> float:
    Total = 0.0
    for FaceValue in BuildShape(Solid).Faces:
        if not isinstance(FaceValue, CapFace):
            Total += SpanLength(FaceValue.Span) * (
                FaceValue.UpperCm - FaceValue.LowerCm
            )
            continue
        Signed = 0.0
        for LoopValue in FaceValue.Loops:
            for UseValue in LoopValue:
                if isinstance(UseValue.Edge, LevelEdge):
                    Amount = SpanArea(UseValue.Edge.Span)
                    Signed += Amount if UseValue.Forward else -Amount
        Total += abs(Signed)
    return Total
