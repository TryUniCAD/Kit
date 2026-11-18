from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyNameGraph import (
    BodyNameGraph,
)
from interchange.brep.Topology.BrepModel import BrepModel


# decoded geometry must exhaust the actual named wire body before its neutral identity is assigned
def CheckBrepTree(ModelValue: BrepModel, GraphValue: BodyNameGraph) -> None:
    TreeValue = GraphValue.TreeValue
    Inventories = (
        (
            "face",
            TreeValue.FaceIds,
            tuple(FaceValue.id for FaceValue in ModelValue.faces),
        ),
        (
            "loop",
            TreeValue.LoopIds,
            tuple(LoopValue.id for LoopValue in ModelValue.loops),
        ),
        ("coedge", TreeValue.FinIds, tuple(Coedge.id for Coedge in ModelValue.coedges)),
        (
            "edge",
            TreeValue.EdgeIds,
            tuple(EdgeValue.id for EdgeValue in ModelValue.edges),
        ),
        (
            "vertex",
            TreeValue.VertexIds,
            tuple(Vertex.id for Vertex in ModelValue.vertices),
        ),
        (
            "surface",
            TreeValue.SurfaceIds,
            tuple(Surface.id for Surface in ModelValue.surfaces),
        ),
        ("curve", TreeValue.CurveIds, tuple(Curve.id for Curve in ModelValue.curves)),
    )
    for KindValue, NativeIds, PublicIds in Inventories:
        if len(NativeIds) != len(PublicIds) or {
            f"sldprt:brep:{KindValue}:{IndexValue + 1}" for IndexValue in NativeIds
        } != set(PublicIds):
            raise ValueError(
                "public brep does not preserve the complete named native inventory"
            )
    Vertices = {Vertex.id: Vertex for Vertex in ModelValue.vertices}
    for IndexValue in TreeValue.VertexIds:
        VertexNode = GraphValue.NodesValue[IndexValue]
        NativePoint = ReadXmtVector(
            RequireXmt(GraphValue.NodesValue, VertexNode.Integer("point"), 29), "pvec"
        )
        PointValue = Vertices[f"sldprt:brep:vertex:{IndexValue + 1}"].point
        if any(
            not IsClose(Actual, Expected * 1000, rel_tol=1e-12, abs_tol=1e-9)
            for Actual, Expected in zip(
                (PointValue.x, PointValue.y, PointValue.z), NativePoint, strict=True
            )
        ):
            raise ValueError(
                "public brep vertex geometry differs from its named native owner"
            )
