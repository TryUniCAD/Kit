from collections.abc import Mapping

from convert.Geometry.Parasolid import BuildPartModel
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.AddCylGeomMut import (
    AddCylGeomMut,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.CheckCylBrep import (
    CheckCylBrep,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.CheckCylGraph import (
    CheckCylGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.MakeLocalBodyTables import (
    MakeLocalTables,
)
from interchange.brep.Topology.BrepModel import BrepModel


# the bare analytic boundary supplies geometry when the active world contains no body
def ReadLocalCyl(
    NodesValue: Mapping[int, XmtNode], OffsetsValue: Mapping[int, int]
) -> BrepModel:
    CheckCylGraph(NodesValue)
    TablesValue = MakeLocalTables(NodesValue, OffsetsValue)
    for NodeValue in NodesValue.values():
        if NodeValue.KindValue in (31, 51):
            AddCylGeomMut(TablesValue, NodeValue)
    ModelValue = BuildPartModel(TablesValue)
    CheckCylBrep(ModelValue)
    return ModelValue
