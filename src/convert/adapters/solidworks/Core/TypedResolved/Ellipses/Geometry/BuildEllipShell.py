from dataclasses import replace as ReplaceValue

from convert.Geometry.Revolve.SweepModel import BuildSweepModel
from convert.adapters.solidworks.Core.TypedResolved.Ellipses.Geometry.EllipBoundary import (
    EllipCurves,
    EllipPcurves,
    EllipSection,
    EllipSurfaces,
    KEllipKnots,
)
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import (
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepLoop,
    BrepVertex,
)
from interchange.geometry.Models.GeometryConics import EllipseGeometry

# each owned trim joins twice to one rim or the two sides of the lateral seam
KEllipUses = (
    ("lower-cap", "lower", "lower", True),
    ("upper-cap", "upper", "upper", False),
    ("bottom", "lower", "bottom", False),
    ("far-seam", "seam", "far-seam", False),
    ("top", "upper", "top", True),
    ("near-seam", "seam", "near-seam", True),
)


# the neutral seam is explicit at its actual lower and upper major stations
def EllipEdges(HeightMm: float) -> tuple[BrepEdge, ...]:
    return (
        BrepEdge(
            "ellipse-lower-edge",
            "ellipse-lower-vertex",
            "ellipse-lower-vertex",
            "ellipse-lower-curve",
            0.0,
            KEllipKnots[-1],
        ),
        BrepEdge(
            "ellipse-upper-edge",
            "ellipse-upper-vertex",
            "ellipse-upper-vertex",
            "ellipse-upper-curve",
            0.0,
            KEllipKnots[-1],
        ),
        BrepEdge(
            "ellipse-seam-edge",
            "ellipse-lower-vertex",
            "ellipse-upper-vertex",
            "ellipse-seam-curve",
            0.0,
            HeightMm,
        ),
    )


# closed wraps require opposite rim senses at their caps and at the cylindrical wall
def BuildEllipShell(
    Ellipse: EllipseGeometry, HeightMm: float, BodyId: str
) -> BrepModel:
    Lower, Upper = EllipSection(Ellipse, 0.0), EllipSection(Ellipse, HeightMm)
    Vertices = (
        BrepVertex("ellipse-lower-vertex", Lower[0]),
        BrepVertex("ellipse-upper-vertex", Upper[0]),
    )
    Loops = (
        BrepLoop("ellipse-lower-loop", ("ellipse-lower-cap-use",), outer=True),
        BrepLoop("ellipse-upper-loop", ("ellipse-upper-cap-use",), outer=True),
        BrepLoop(
            "ellipse-wall-loop",
            tuple(f"ellipse-{RoleValue}-use" for RoleValue, _, _, _ in KEllipUses[2:]),
            outer=True,
        ),
    )
    Faces = tuple(
        BrepFace(
            f"ellipse-{RoleValue}-face", f"ellipse-{RoleValue}-surface", (LoopValue.id,)
        )
        for RoleValue, LoopValue in zip(("lower", "upper", "wall"), Loops, strict=True)
    )
    Model = BuildSweepModel(
        BodyId,
        "ellipse",
        EllipCurves(Lower, Upper),
        EllipSurfaces(Ellipse, Lower, Upper),
        Vertices,
        EllipEdges(HeightMm),
        Faces,
        Loops,
        tuple(
            BrepCoedge(
                f"ellipse-{RoleValue}-use",
                f"ellipse-{EdgeValue}-edge",
                reversed=ReversedValue,
            )
            for RoleValue, EdgeValue, _, ReversedValue in KEllipUses
        ),
    )
    Trimmed = ReplaceValue(
        Model,
        pcurves=EllipPcurves(Ellipse, HeightMm),
        coedges=tuple(
            ReplaceValue(Value, pcurve_id=f"ellipse-{TrimValue}-trim")
            for Value, (_, _, TrimValue, _) in zip(
                Model.coedges, KEllipUses, strict=True
            )
        ),
    )
    if Trimmed.validate(frozenset((BodyId,))):
        raise ValueError("exact elliptical sweep trims failed neutral body validation")
    return Trimmed
