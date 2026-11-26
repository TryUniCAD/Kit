from types import MappingProxyType

from convert.adapters.solidworks.Archive.Partition.MakeXmtShape import MakeXmtShape

# declared kernel fields preserve exact typed ownership without saved record values
KBoundaryShapes = MappingProxyType(
    {
        14: MakeXmtShape(
            "FACE",
            "node_id:d attributes_features:p1019 tolerance:f next:p14 previous:p14 loop:p15 shell:p13 surface:p1006 sense:c next_on_surface:p14 previous_on_surface:p14 next_front:p14 previous_front:p14 front_shell:p13",
        ),
        15: MakeXmtShape(
            "LOOP", "node_id:d attributes_features:p1019 halfedge:p17 face:p14 next:p15"
        ),
        16: MakeXmtShape(
            "EDGE",
            "node_id:d attributes_features:p1019 tolerance:f halfedge:p17 previous:p16 next:p16 curve:p1008 next_on_curve:p16 previous_on_curve:p16 owner:p1029",
        ),
        17: MakeXmtShape(
            "HALFEDGE",
            "attributes_features:p1019 loop:p15 forward:p17 backward:p17 vertex:p18 other:p17 edge:p16 curve:p1008 next_at_vx:p17 sense:c",
        ),
        18: MakeXmtShape(
            "VERTEX",
            "node_id:d attributes_features:p1019 halfedge:p17 previous:p18 next:p18 point:p29 tolerance:f owner:p1029",
        ),
    }
)
