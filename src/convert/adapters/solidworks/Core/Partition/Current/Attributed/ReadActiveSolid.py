from convert.Geometry.Parasolid import BuildPartModel, CollectPartTopo
from convert.adapters.solidworks.Archive.Partition.Current.Attributed.ReadActiveRows import (
    ReadActiveRows,
)
from convert.adapters.solidworks.Core.Partition.Current.Attributed.CheckOwnedAttrs import (
    CheckOwnedAttrs,
)
from convert.adapters.solidworks.Core.Partition.Current.Attributed.CheckActiveBody import (
    CheckActiveBody,
)
from convert.adapters.solidworks.Core.Partition.Current.Attributed.ReadFaceAttrs import (
    ReadFaceAttrs,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.MakeLocalBodyTables import (
    MakeLocalTables,
)
from interchange.brep.Topology.BrepModel import BrepModel


# proven typed active records can recover geometry after the legacy paths decline
def ReadActiveSolid(DataValue: bytes) -> BrepModel:
    Nodes, Offsets = ReadActiveRows(DataValue)
    BodyValue, Kinds = CheckActiveBody(Nodes)
    Heads = CheckOwnedAttrs(Nodes, BodyValue, Kinds)
    Unchanged, Orders = ReadFaceAttrs(Nodes, Heads, Kinds[14])
    Tables = MakeLocalTables(Nodes, Offsets)
    *_, NewVertices, NewCurves, _ = CollectPartTopo(Tables)
    if NewVertices or NewCurves:
        raise ValueError("attributed active projection uses synthetic geometry")
    Model = BuildPartModel(Tables, Unchanged, Orders)
    if (
        len(Model.bodies) != 1
        or len(Model.regions) != 1
        or not Model.regions[0].solid
        or len(Model.shells) != 1
        or not Model.shells[0].closed
        or len(Model.faces) != len(Tables.bridges)
        or len(Model.loops) != len(Tables.loops)
        or len(Model.edges) != len(Tables.edge_uses)
        or len(Model.coedges) != len(Tables.coedges)
        or len(Model.vertices) != len(Tables.vertex_uses)
        or len(Model.curves) != len(Tables.curves)
        or len(Model.surfaces) != len(Tables.surfaces)
        or Model.validate()
    ):
        raise ValueError(
            "attributed active graph does not project one complete closed solid"
        )
    return Model
