from typing import cast as CastValue

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
    FormEdge,
    FormFace,
    FormSurface,
    FormUse,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineKnot import SplineKnot

KCubeVertices: tuple[KJournalVector, ...] = (
    (0.0, 0.0, 0.0),
    (1.0, 0.0, 0.0),
    (1.0, 1.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
    (1.0, 0.0, 1.0),
    (1.0, 1.0, 1.0),
    (0.0, 1.0, 1.0),
)
KCubeFaceLoops = (
    (0, 3, 2, 1),
    (4, 5, 6, 7),
    (0, 1, 5, 4),
    (1, 2, 6, 5),
    (2, 3, 7, 6),
    (3, 0, 4, 7),
)
KCubeParams = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
KCubePlaces = (0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0)
KCubeKnots = (SplineKnot(0.0, 3), SplineKnot(1.0, 3))
KCubeRegions = tuple(
    (PatchCell(FaceIndex, (0.0, 1.0, 0.0, 1.0), (0.0, 0.0, 0)),)
    for FaceIndex in range(len(KCubeFaceLoops))
)


def MakeCurve(Start: tuple[float, ...], Final: tuple[float, ...]) -> BsCurve:
    Poles = tuple(
        tuple(
            Start[AxisIndex] + Place * (Final[AxisIndex] - Start[AxisIndex])
            for AxisIndex in range(len(Start))
        )
        for Place in KCubePlaces
    )
    return BsCurve(False, 3, 0, (0.0, 1.0), (3, 3), len(Start), Poles, ())


def MakePoint(
    Origin: KJournalVector,
    AlongU: KJournalVector,
    AlongV: KJournalVector,
    ParamU: float,
    ParamV: float,
) -> KJournalVector:
    return CastValue(
        KJournalVector,
        tuple(
            Origin[AxisIndex] + ParamU * AlongU[AxisIndex] + ParamV * AlongV[AxisIndex]
            for AxisIndex in range(3)
        ),
    )


def MakeDelta(Start: KJournalVector, Final: KJournalVector) -> KJournalVector:
    return CastValue(
        KJournalVector,
        tuple(Final[AxisIndex] - Start[AxisIndex] for AxisIndex in range(3)),
    )


def MakeSurface(FaceLoop: tuple[int, int, int, int], Region: int) -> FormSurface:
    Origin = KCubeVertices[FaceLoop[0]]
    AlongU = MakeDelta(Origin, KCubeVertices[FaceLoop[1]])
    AlongV = MakeDelta(Origin, KCubeVertices[FaceLoop[3]])
    Points = tuple(
        MakePoint(Origin, AlongU, AlongV, ParamU, ParamV)
        for ParamV in KCubePlaces
        for ParamU in KCubePlaces
    )
    Cache = NubsSurface(3, 3, 0, 0, 0, 0, KCubeKnots, KCubeKnots, Points)
    return FormSurface(Cache, ((), (), (), (), (), ()), Region)


def MakeCube() -> FormBody:
    EdgePlaces: dict[tuple[int, int], int] = {}
    Edges: list[FormEdge] = []
    Faces: list[FormFace] = []
    for Region, FaceLoop in enumerate(KCubeFaceLoops):
        FaceUses: list[FormUse] = []
        for ParamIndex, ParamStart in enumerate(KCubeParams):
            Start = FaceLoop[ParamIndex]
            Final = FaceLoop[(ParamIndex + 1) % len(FaceLoop)]
            EdgeKey = (min(Start, Final), max(Start, Final))
            if EdgeKey not in EdgePlaces:
                EdgePlaces[EdgeKey] = len(Edges)
                Curve = MakeCurve(KCubeVertices[Start], KCubeVertices[Final])
                Edges.append(FormEdge(Start, Final, Curve, ((), (), ())))
            EdgeIndex = EdgePlaces[EdgeKey]
            ParamFinal = KCubeParams[(ParamIndex + 1) % len(KCubeParams)]
            Reversed = Start != Edges[EdgeIndex].StartVertex
            FaceUses.append(
                FormUse(EdgeIndex, Reversed, MakeCurve(ParamStart, ParamFinal))
            )
        Surface = MakeSurface(FaceLoop, Region)
        Faces.append(FormFace(Surface, tuple(FaceUses), str(Region + 1)))
    return FormBody(KCubeVertices, tuple(Edges), tuple(Faces), KCubeRegions)
