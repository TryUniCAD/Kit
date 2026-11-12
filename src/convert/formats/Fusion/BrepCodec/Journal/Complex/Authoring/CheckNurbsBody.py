from collections import Counter as CountItems

from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NurbsBody import (
    NurbsBody,
    NurbsEdge,
    NurbsFace,
    NurbsUse,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.SplineEval import (
    PointOnCurve,
    PointOnSurface,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckBsCurve import (
    CheckBsCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckBsSurface import (
    CheckBsSurface,
)

KTolerance = 1e-6


def IsNear(First: tuple[float, ...], Second: tuple[float, ...]) -> bool:
    return len(First) == len(Second) and all(
        abs(Former - Latter) <= KTolerance for Former, Latter in zip(First, Second)
    )


def UseEnds(Model: NurbsBody, UseSpec: NurbsUse) -> tuple[int, int]:
    EdgeSpec = Model.Edges[UseSpec.EdgeIndex]
    if UseSpec.Reversed:
        return EdgeSpec.EndVertex, EdgeSpec.StartVertex
    return EdgeSpec.StartVertex, EdgeSpec.EndVertex


def CheckNurbsEdge(Model: NurbsBody, EdgeSpec: NurbsEdge) -> None:
    CheckBsCurve(EdgeSpec.Curve, 3)
    Lower, Upper = EdgeSpec.Curve.Knots[0], EdgeSpec.Curve.Knots[-1]
    if not (
        IsNear(
            PointOnCurve(EdgeSpec.Curve, Lower), Model.PointsCm[EdgeSpec.StartVertex]
        )
        and IsNear(
            PointOnCurve(EdgeSpec.Curve, Upper), Model.PointsCm[EdgeSpec.EndVertex]
        )
    ):
        raise ValueError("Fusion NURBS edge curve does not meet its vertices")


def CheckNurbsUse(Model: NurbsBody, FaceSpec: NurbsFace, UseSpec: NurbsUse) -> None:
    Curve = Model.Edges[UseSpec.EdgeIndex].Curve
    CheckBsCurve(UseSpec.Pcurve, 2)
    Lower, Upper = Curve.Knots[0], Curve.Knots[-1]
    if (UseSpec.Pcurve.Knots[0], UseSpec.Pcurve.Knots[-1]) != (Lower, Upper):
        raise ValueError("Fusion NURBS pcurve range must equal its edge range")
    Samples = {Lower + (Upper - Lower) * StepIndex / 16.0 for StepIndex in range(17)}
    for Parameter in sorted(Samples | set(Curve.Knots) | set(UseSpec.Pcurve.Knots)):
        UValue, VValue = PointOnCurve(UseSpec.Pcurve, Parameter)
        if not IsNear(
            PointOnSurface(FaceSpec.Surface, UValue, VValue),
            PointOnCurve(Curve, Parameter),
        ):
            raise ValueError("Fusion NURBS pcurve leaves its edge on the surface")


def CheckNurbsLoop(Model: NurbsBody, FaceSpec: NurbsFace) -> None:
    CheckBsSurface(FaceSpec.Surface)
    if not FaceSpec.Uses:
        raise ValueError("Fusion NURBS face requires one bounded loop")
    for Index, UseSpec in enumerate(FaceSpec.Uses):
        Following = FaceSpec.Uses[(Index + 1) % len(FaceSpec.Uses)]
        if UseEnds(Model, UseSpec)[1] != UseEnds(Model, Following)[0]:
            raise ValueError("Fusion NURBS loop uses do not connect")
        CheckNurbsUse(Model, FaceSpec, UseSpec)


def CheckNurbsBody(Model: NurbsBody) -> None:
    if not Model.Faces or not Model.Edges or not 2 <= len(Model.PointsCm) <= 4096:
        raise ValueError("Fusion NURBS body requires faces, edges and vertices")
    Vertices = {
        Vertex
        for EdgeSpec in Model.Edges
        for Vertex in (EdgeSpec.StartVertex, EdgeSpec.EndVertex)
    }
    if Vertices != set(range(len(Model.PointsCm))):
        raise ValueError("Fusion NURBS vertices must all bound some edge")
    UseSpecs = tuple(UseSpec for FaceSpec in Model.Faces for UseSpec in FaceSpec.Uses)
    Counts = CountItems(UseSpec.EdgeIndex for UseSpec in UseSpecs)
    if set(Counts) != set(range(len(Model.Edges))) or set(Counts.values()) not in (
        {1},
        {2},
    ):
        raise ValueError("Fusion NURBS body must be one open sheet or one closed shell")
    for EdgeIndex, Count in Counts.items():
        Senses = {
            UseSpec.Reversed for UseSpec in UseSpecs if UseSpec.EdgeIndex == EdgeIndex
        }
        if Count == 2 and Senses != {False, True}:
            raise ValueError("Fusion NURBS shared edge needs opposite coedge senses")
    for EdgeSpec in Model.Edges:
        CheckNurbsEdge(Model, EdgeSpec)
    for FaceSpec in Model.Faces:
        CheckNurbsLoop(Model, FaceSpec)
