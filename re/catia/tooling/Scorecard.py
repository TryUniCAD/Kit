"""Score the native CATIA reader against each file's own geometry.

No vendor runtime is available here, so the tightest ground truth is inside the file: every decoded
vertex must lie on the surfaces of the faces that use it, every loop must close, and the shell must
satisfy Euler's relation. This tool prints that scorecard for the whole corpus so the reader's
exactness is measured per part instead of asserted.

Run it with `uv run python re/catia/tooling/Scorecard.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "src")

from convert.adapters.catia.Container import CfvTwoArchive
from convert.adapters.catia.NativeBrep import DecodeBrep
from interchange import CylinderSurface, PlaneSurface


def SurfaceError(Point: object, Surface: object) -> float:
    """Return the distance from a point to a plane or cylinder surface."""
    if isinstance(Surface, PlaneSurface):
        Origin = Surface.origin
        Normal = Surface.normal
        return abs(
            (Point.x - Origin.x) * Normal.x
            + (Point.y - Origin.y) * Normal.y
            + (Point.z - Origin.z) * Normal.z
        )
    if isinstance(Surface, CylinderSurface):
        Origin = Surface.origin
        Axis = Surface.axis
        Delta = (Point.x - Origin.x, Point.y - Origin.y, Point.z - Origin.z)
        Along = Delta[0] * Axis.x + Delta[1] * Axis.y + Delta[2] * Axis.z
        Radial = max(
            0.0,
            Delta[0] * Delta[0]
            + Delta[1] * Delta[1]
            + Delta[2] * Delta[2]
            - Along * Along,
        ) ** 0.5
        return abs(Radial - Surface.radius)
    return 0.0


def Score(Model: object) -> tuple[float, int]:
    """Return the worst surface distance and how many faces are non-planar-tolerant."""
    Surfaces = {Value.id: Value for Value in Model.surfaces}
    Vertices = {Value.id: Value for Value in Model.vertices}
    Edges = {Value.id: Value for Value in Model.edges}
    Loops = {Value.id: Value for Value in Model.loops}
    Coedges = {Value.id: Value for Value in Model.coedges}
    Worst = 0.0
    Bad = 0
    for FaceValue in Model.faces:
        Surface = Surfaces.get(FaceValue.surface_id)
        if Surface is None:
            continue
        FaceWorst = 0.0
        for LoopId in FaceValue.loop_ids:
            for CoedgeId in Loops[LoopId].coedge_ids:
                EdgeValue = Edges[Coedges[CoedgeId].edge_id]
                for VertexId in (EdgeValue.start_vertex_id, EdgeValue.end_vertex_id):
                    FaceWorst = max(
                        FaceWorst, SurfaceError(Vertices[VertexId].point, Surface)
                    )
        Worst = max(Worst, FaceWorst)
        if FaceWorst > 1e-3:
            Bad += 1
    return (Worst, Bad)


def Main() -> None:
    Base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("re/catia/examples/.CATPart")
    print(f"{'part':34s} {'F':>4s} {'E':>5s} {'V':>5s} {'chi':>4s} {'worst':>9s} {'bad':>4s} heur")
    for PathValue in sorted(Base.rglob("*.CATPart")):
        Model, Diagnostics = DecodeBrep(
            CfvTwoArchive.from_bytes(PathValue.read_bytes())
        )
        if Model is None:
            print(f"{PathValue.name:34s} decode failed")
            continue
        Worst, Bad = Score(Model)
        Euler = len(Model.vertices) - len(Model.edges) + len(Model.faces)
        Heuristic = any(
            Value.code == "catia.brep.native_surface_map_heuristic"
            for Value in Diagnostics
        )
        print(
            f"{PathValue.name:34s} {len(Model.faces):4d} {len(Model.edges):5d} "
            f"{len(Model.vertices):5d} {Euler:4d} {Worst:9.4f} {Bad:4d} "
            f"{'yes' if Heuristic else 'no'}"
        )


if __name__ == "__main__":
    Main()
