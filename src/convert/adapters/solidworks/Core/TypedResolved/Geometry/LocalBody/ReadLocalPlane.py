from collections.abc import Mapping

from convert.Geometry.Parasolid import BrepTopology, BuildPartModel
from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckPocket import (
    CheckPocket,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckPrismTrims import (
    CheckPrismTrims,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.OrientPocket import (
    OrientPocket,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCarriers import (
    ReadCarriers,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.ReadPrismFaces import (
    ReadPrismFaces,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.CheckLocalBodyGraph import (
    CheckLocalGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.MakeLocalBodyTables import (
    MakeLocalTables,
)
from interchange.brep.Topology.BrepModel import BrepModel


# all imported plane and line records must be realized by one complete closed boundary
def ReadLocalPlane(
    NodesValue: Mapping[int, XmtNode],
    OffsetsValue: Mapping[int, int],
    *,
    AllowPocket: bool,
) -> BrepModel:
    CheckLocalGraph(NodesValue, AllowPocket=AllowPocket)
    TablesValue = MakeLocalTables(NodesValue, OffsetsValue)
    ModelValue = BuildPartModel(TablesValue)
    if (
        len(ModelValue.bodies) != 1
        or len(ModelValue.regions) != 1
        or not ModelValue.regions[0].solid
        or len(ModelValue.shells) != 1
        or not ModelValue.shells[0].closed
        or len(ModelValue.faces) != len(TablesValue.bridges)
        or len(ModelValue.loops) != len(TablesValue.loops)
        or len(ModelValue.edges) != len(TablesValue.edge_uses)
        or len(ModelValue.coedges) != len(TablesValue.coedges)
        or len(ModelValue.vertices) != len(TablesValue.vertex_uses)
        or len(ModelValue.curves) != len(TablesValue.curves)
        or len(ModelValue.surfaces) != len(TablesValue.surfaces)
        or ModelValue.validate()
    ):
        raise ValueError("local body does not contain one complete closed solid")
    if AllowPocket:
        Oriented = OrientPocket(ModelValue)
        TopologyValue = BrepTopology(Oriented)
        CheckPrismTrims(TopologyValue, ReadCarriers(Oriented))
        Boundaries = ReadPrismFaces(Oriented, TopologyValue, AllowPocket=True)
        CheckPocket(Oriented, TopologyValue, Boundaries)
    return ModelValue
