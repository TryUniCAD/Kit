from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.ExactSubtypes import (
    ExactCurve,
    ExactSurface,
    ParamCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NegateCurve import (
    NegateCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NurbsBody import (
    NurbsBody,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NurbsLayout import (
    NurbsLayout,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.IntcurveNode import (
    IntcurveNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode

KBlankPrefix = EntityPrefix(-1, -1)


def MakeNurbsFaces(
    Model: NurbsBody, Layout: NurbsLayout
) -> tuple[FaceNode | LoopNode | SplineNode, ...]:
    FaceCount = len(Model.Faces)
    Faces = tuple(
        FaceNode(
            KBlankPrefix,
            Layout.FaceBase + Index + 1 if Index + 1 < FaceCount else -1,
            Layout.LoopBase + Index,
            3,
            Layout.SurfaceBase + Index,
            False,
            False,
            None,
        )
        for Index in range(FaceCount)
    )
    Loops = tuple(
        LoopNode(
            KBlankPrefix,
            -1,
            Layout.CoedgeBase + Layout.UseStarts[Index],
            Layout.FaceBase + Index,
        )
        for Index in range(FaceCount)
    )
    Surfaces = tuple(
        SplineNode(
            KBlankPrefix, False, ExactSurface(FaceSpec.Surface), None, None, None, None
        )
        for FaceSpec in Model.Faces
    )
    return (*Faces, *Loops, *Surfaces)


def MakeNurbsUses(Model: NurbsBody, Layout: NurbsLayout) -> tuple[CoedgeNode, ...]:
    Slots = tuple(
        (FaceIndex, Offset, UseSpec)
        for FaceIndex, FaceSpec in enumerate(Model.Faces)
        for Offset, UseSpec in enumerate(FaceSpec.Uses)
    )
    Results: list[CoedgeNode] = []
    for Global, (FaceIndex, Offset, UseSpec) in enumerate(Slots):
        Start = Layout.CoedgeBase + Layout.UseStarts[FaceIndex]
        Length = len(Model.Faces[FaceIndex].Uses)
        Partner = next(
            (
                Layout.CoedgeBase + Other
                for Other, (_, _, Candidate) in enumerate(Slots)
                if Other != Global and Candidate.EdgeIndex == UseSpec.EdgeIndex
            ),
            -1,
        )
        Results.append(
            CoedgeNode(
                KBlankPrefix,
                Start + (Offset + 1) % Length,
                Start + (Offset - 1) % Length,
                Partner,
                Layout.EdgeBase + UseSpec.EdgeIndex,
                UseSpec.Reversed,
                Layout.LoopBase + FaceIndex,
                Layout.PcurveBase + Global,
            )
        )
    return tuple(Results)


def MakeNurbsEdges(
    Model: NurbsBody, Layout: NurbsLayout, Coedges: tuple[CoedgeNode, ...]
) -> tuple[EdgeNode | VertexNode | PointNode, ...]:
    Edges = tuple(
        EdgeNode(
            KBlankPrefix,
            Layout.VertexBase + EdgeSpec.StartVertex,
            EdgeSpec.Curve.Knots[0],
            Layout.VertexBase + EdgeSpec.EndVertex,
            EdgeSpec.Curve.Knots[-1],
            Layout.CoedgeBase
            + next(
                Ordinal
                for Ordinal, Coedge in enumerate(Coedges)
                if Coedge.EdgeRef == Layout.EdgeBase + Index
            ),
            Layout.CurveBase + Index,
            False,
            "unknown",
        )
        for Index, EdgeSpec in enumerate(Model.Edges)
    )
    Owners = tuple(
        next(
            (Index, 0 if EdgeSpec.StartVertex == Vertex else 1)
            for Index, EdgeSpec in enumerate(Model.Edges)
            if Vertex in (EdgeSpec.StartVertex, EdgeSpec.EndVertex)
        )
        for Vertex in range(len(Model.PointsCm))
    )
    Vertices = tuple(
        VertexNode(
            KBlankPrefix, Layout.EdgeBase + Owner, EdgeEnd, Layout.PointBase + Vertex
        )
        for Vertex, (Owner, EdgeEnd) in enumerate(Owners)
    )
    Points = tuple(PointNode(KBlankPrefix, Point) for Point in Model.PointsCm)
    return (*Edges, *Vertices, *Points)


def MakeNurbsCurves(Model: NurbsBody) -> tuple[PcurveNode | IntcurveNode, ...]:
    Pcurves = tuple(
        PcurveNode(
            KBlankPrefix,
            0,
            False,
            ParamCurve(
                NegateCurve(UseSpec.Pcurve) if UseSpec.Reversed else UseSpec.Pcurve,
                FaceIndex,
            ),
            -1,
            0.0,
            0.0,
        )
        for FaceIndex, FaceSpec in enumerate(Model.Faces)
        for UseSpec in FaceSpec.Uses
    )
    Curves = tuple(
        IntcurveNode(
            KBlankPrefix,
            False,
            ExactCurve(EdgeSpec.Curve),
            EdgeSpec.Curve.Knots[0],
            EdgeSpec.Curve.Knots[-1],
        )
        for EdgeSpec in Model.Edges
    )
    return (*Pcurves, *Curves)
