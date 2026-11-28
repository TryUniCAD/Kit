from collections.abc import Mapping
from dataclasses import replace as Replace
from math import tau as FullTurn

from convert.Geometry.Parasolid import BuildPartModel
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.CheckAnnBrep import (
    CheckAnnBrep,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.AddCylGeomMut import (
    AddCylGeomMut,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.BindAnnRoles import (
    BindAnnRoles,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.CheckAnnGraph import (
    HasAnnularWalls,
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


# the proved vertex free rings own complete periods independent of reconstructed seam rounding
def ReadLocalCyl(
    NodesValue: Mapping[int, XmtNode], OffsetsValue: Mapping[int, int]
) -> BrepModel:
    CheckCylGraph(NodesValue)
    TablesValue = MakeLocalTables(NodesValue, OffsetsValue)
    for NodeValue in NodesValue.values():
        if NodeValue.KindValue in (31, 51):
            AddCylGeomMut(TablesValue, NodeValue)
    ModelValue = BuildPartModel(TablesValue)
    ModelValue = Replace(
        ModelValue,
        edges=tuple(
            Replace(EdgeValue, start_parameter=0.0, end_parameter=FullTurn)
            for EdgeValue in ModelValue.edges
        ),
    )
    if HasAnnularWalls(NodesValue):
        ModelValue = BindAnnRoles(ModelValue)
        CheckAnnBrep(ModelValue)
    else:
        CheckCylBrep(ModelValue)
    return ModelValue
