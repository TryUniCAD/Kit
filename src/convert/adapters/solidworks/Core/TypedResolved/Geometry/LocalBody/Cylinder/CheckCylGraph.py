from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.CheckAnnGraph import (
    CheckAnnGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.CheckCylRims import (
    CheckCylRims,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalRoot import (
    ReadLocalRoot,
)

# the bare periodic profile has no ignored active topology or carrier switches
KInactiveLinks = {
    12: (
        "attribute_chains",
        "surface",
        "curve",
        "point",
        "key",
        "boundary_point",
        "vertex",
        "index_map_offset",
        "index_map",
        "node_id_index_map",
        "schema_embedding_map",
        "lowest_node_id",
        "mesh_offset_data",
    ),
    13: ("next", "edge", "vertex"),
    14: ("next_on_surface", "previous_on_surface"),
    16: ("next_on_curve", "previous_on_curve"),
    17: ("vertex", "curve", "next_at_vx"),
    19: ("frame", "owner"),
    31: ("geometric_owner",),
    50: ("geometric_owner",),
    51: ("geometric_owner",),
}


# admitting the periodic shape requires every resident entity to be accounted for
def CheckCylGraph(NodesValue: Mapping[int, XmtNode]) -> None:
    BodyValue, KindsValue = ReadLocalRoot(NodesValue, False)
    WallCount = len(KindsValue.get(51, ()))
    Inventory = {
        12: 1,
        13: 2,
        14: WallCount + 2,
        15: 4 * WallCount,
        16: 2 * WallCount,
        17: 4 * WallCount,
        19: 2,
        31: 2 * WallCount,
        50: 2,
        51: WallCount,
    }
    if {
        KindValue: len(IdsValue) for KindValue, IdsValue in KindsValue.items()
    } != Inventory or tuple(NodesValue) != tuple(range(1, len(NodesValue) + 1)):
        raise ValueError("local cylinder has an unqualified resident node inventory")
    ExpectedIds = len(NodesValue) - Inventory[12] - Inventory[17]
    if (
        BodyValue.Integer("highest_node_id") != ExpectedIds
        or BodyValue.Integer("state") != 1
        or BodyValue.Integer("nom_geom_state") != 1
        or {
            NodeValue.Integer("node_id")
            for NodeValue in NodesValue.values()
            if NodeValue.KindValue not in (12, 17)
        }
        != set(range(1, ExpectedIds + 1))
        or any(
            NodeValue.Integer(FieldName)
            for NodeValue in NodesValue.values()
            for FieldName in (
                "attributes_features",
                *KInactiveLinks.get(NodeValue.KindValue, ()),
            )
        )
    ):
        raise ValueError("local cylinder has unqualified bare ownership or identities")
    if WallCount > 1:
        CheckAnnGraph(NodesValue, BodyValue, WallCount)
    else:
        CheckCylRims(NodesValue, BodyValue)
