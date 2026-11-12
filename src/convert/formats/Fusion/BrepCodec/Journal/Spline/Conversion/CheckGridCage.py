from convert.formats.Fusion.TSplineCodec.Model.GripMapping import GripMapping
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface

KWeightSlack = 2.0**-51


def CheckGridCage(Surface: TsplineSurface) -> GripMapping:
    Header, Topology = Surface.Header, Surface.Topology
    if (Header.Degree, Header.UnitScale, Header.EndConditions) != (
        3,
        1.0,
        "SUBD_CREASES",
    ):
        raise ValueError("Fusion grid conversion needs the cubic crease profile")
    if Surface.Mapping is None:
        raise ValueError("Fusion grid conversion needs boundary compound grips")
    if any(CageEdge.KnotInterval != 1.0 for CageEdge in Topology.Edges):
        raise ValueError("Fusion grid conversion needs unit knot intervals")
    if any(Condition.EndValue != 0.0 for Condition in Topology.EndConditions):
        raise ValueError("Fusion grid conversion needs zero end conditions")
    if any(abs(GripValue.Weight - 1.0) > KWeightSlack for GripValue in Surface.Grips):
        raise ValueError("Fusion grid conversion needs unit grip weights")
    RimEdges = {
        LinkValue.EdgeIndex for LinkValue in Topology.Links if LinkValue.FaceIndex == -1
    }
    RimVertices = {
        LinkValue.VertexIndex
        for LinkValue in Topology.Links
        if LinkValue.FaceIndex == -1
    }
    Creases = Surface.Creases
    if Creases is not None and (
        not set(Creases.EdgeIndices) <= RimEdges
        or not set(Creases.VertexIndices) <= RimVertices
    ):
        raise ValueError("Fusion grid conversion does not convert interior creases")
    return Surface.Mapping
