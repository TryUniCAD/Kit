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
    if any(Edge.KnotInterval != 1.0 for Edge in Topology.Edges):
        raise ValueError("Fusion grid conversion needs unit knot intervals")
    if any(Condition.EndValue != 0.0 for Condition in Topology.EndConditions):
        raise ValueError("Fusion grid conversion needs zero end conditions")
    if any(abs(Grip.Weight - 1.0) > KWeightSlack for Grip in Surface.Grips):
        raise ValueError("Fusion grid conversion needs unit grip weights")
    Edges = {Link.EdgeIndex for Link in Topology.Links if Link.FaceIndex == -1}
    Corners = {Link.VertexIndex for Link in Topology.Links if Link.FaceIndex == -1}
    Creases = Surface.Creases
    if Creases is not None and (
        not set(Creases.EdgeIndices) <= Edges
        or not set(Creases.VertexIndices) <= Corners
    ):
        raise ValueError("Fusion grid conversion does not convert interior creases")
    return Surface.Mapping
