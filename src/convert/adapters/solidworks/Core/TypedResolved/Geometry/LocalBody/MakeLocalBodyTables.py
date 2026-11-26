from collections.abc import Mapping
from math import isfinite as IsFinite
from struct import pack as PackValue

from convert.Geometry.Parasolid import (
    AnalyticPoint,
    ReadTolerance,
    RecordTables,
    TopologyRecord,
)
from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.MakeLocalCarriers import (
    AddLocalGeomMut,
)

# neutral topology uses the existing record table order for each typed native relation
KLocalTopoFields = {
    14: (
        "next",
        "previous",
        "loop",
        "shell",
        "surface",
        "next_on_surface",
        "previous_on_surface",
        "next_front",
        "previous_front",
        "front_shell",
    ),
    15: ("attributes_features", "halfedge", "face", "next"),
    16: ("halfedge", "previous", "next", "curve", "next_on_curve", "previous_on_curve"),
    17: (
        "attributes_features",
        "loop",
        "forward",
        "backward",
        "vertex",
        "other",
        "edge",
        "curve",
        "next_at_vx",
    ),
    18: ("attributes_features", "halfedge", "previous", "next", "point"),
    29: ("attributes_features", "owner", "next", "previous"),
}


# topology records need the encoded reference domain expected by the shared neutral builder
def MakeLocalTopo(NodeValue: XmtNode, OffsetValue: int) -> TopologyRecord:
    KindValue = NodeValue.KindValue
    Values = NodeValue.FieldsValue
    RawTolerance = Values.get("tolerance", 0.0)
    if (
        type(RawTolerance) is not float
        or (Tolerance := ReadTolerance(PackValue(">d", RawTolerance), 0)) is None
    ):
        raise ValueError("local body has an unsupported topology tolerance")
    SenseValue = Values.get("sense", "+")
    if SenseValue not in ("+", "-"):
        raise ValueError("local body has an invalid boundary sense")
    PointValue = None
    if KindValue == 29:
        VectorValue = ReadXmtVector(NodeValue, "pvec")
        if any(
            not IsFinite(Component) or abs(Component) > 10000
            for Component in VectorValue
        ):
            raise ValueError("local body point has invalid coordinates")
        PointValue = AnalyticPoint(VectorValue)
    return TopologyRecord(
        NodeValue.IndexValue + 1,
        tuple(
            NodeValue.Integer(NameValue) + 1
            for NameValue in KLocalTopoFields[KindValue]
        ),
        OffsetValue,
        SenseValue == "-",
        point=PointValue,
        tolerance=Tolerance,
    )


# the local projection shares neutral construction without scanning for native records
def MakeLocalTables(
    NodesValue: Mapping[int, XmtNode], OffsetsValue: Mapping[int, int]
) -> RecordTables:
    TablesValue = RecordTables(
        {}, {}, {}, {}, {}, {}, {}, {}, {}, terminal_fin_vertices=True
    )
    Destinations = {
        14: TablesValue.bridges,
        15: TablesValue.loops,
        16: TablesValue.edge_uses,
        17: TablesValue.coedges,
        18: TablesValue.vertex_uses,
        29: TablesValue.points,
    }
    for IndexValue, NodeValue in NodesValue.items():
        KindValue = NodeValue.KindValue
        if KindValue in Destinations:
            Destinations[KindValue][IndexValue + 1] = MakeLocalTopo(
                NodeValue, OffsetsValue[IndexValue]
            )
        elif KindValue in (30, 50):
            AddLocalGeomMut(TablesValue, NodeValue)
    return TablesValue
