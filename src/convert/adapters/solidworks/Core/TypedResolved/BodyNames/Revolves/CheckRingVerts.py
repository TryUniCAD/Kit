from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyNameGraph import (
    BodyNameGraph,
)
from interchange.brep.Topology.BrepModel import BrepModel


# decoded closed circles use deterministic seam vertices without pretending that native vertex records were transmitted
def CheckRingVerts(ModelValue: BrepModel, GraphValue: BodyNameGraph) -> None:
    TreeValue = GraphValue.TreeValue
    if TreeValue.VertexIds or TreeValue.PointIds or len(TreeValue.EdgeIds) != 4:
        raise ValueError("closed-circle binding has an unqualified native inventory")
    Vertices = {Vertex.id: Vertex for Vertex in ModelValue.vertices}
    Edges = {EdgeValue.id: EdgeValue for EdgeValue in ModelValue.edges}
    if set(Vertices) != {
        f"sldprt:brep:vertex:{65536 + IndexValue + 1}"
        for IndexValue in TreeValue.EdgeIds
    }:
        raise ValueError(
            "closed-circle binding has extra or missing derived seam vertices"
        )
    for IndexValue in TreeValue.EdgeIds:
        EdgeNode = RequireXmt(GraphValue.NodesValue, IndexValue, 16)
        CurveNode = RequireXmt(GraphValue.NodesValue, EdgeNode.Integer("curve"), 31)
        VertexId = f"sldprt:brep:vertex:{65536 + IndexValue + 1}"
        EdgeValue = Edges[f"sldprt:brep:edge:{IndexValue + 1}"]
        if (
            EdgeValue.start_vertex_id != VertexId
            or EdgeValue.end_vertex_id != VertexId
            or EdgeValue.curve_id != f"sldprt:brep:curve:{CurveNode.IndexValue + 1}"
        ):
            raise ValueError(
                "closed-circle endpoints do not retain their actual native edge"
            )
        Centre = ReadXmtVector(CurveNode, "centre")
        Direction = ReadXmtVector(CurveNode, "x_axis")
        RadiusValue = CurveNode.FieldsValue.get("radius")
        if type(RadiusValue) is not float or RadiusValue <= 0:
            raise ValueError("closed-circle radius is unqualified")
        PointValue = Vertices[VertexId].point
        if any(
            not IsClose(
                Actual,
                (Origin + RadiusValue * AxisValue) * 1000,
                rel_tol=1e-12,
                abs_tol=1e-9,
            )
            for Actual, Origin, AxisValue in zip(
                (PointValue.x, PointValue.y, PointValue.z),
                Centre,
                Direction,
                strict=True,
            )
        ):
            raise ValueError(
                "derived closed-circle seam differs from the actual carrier"
            )
