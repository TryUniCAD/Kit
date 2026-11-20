from types import MappingProxyType

from convert.adapters.solidworks.Archive.Partition.MakeXmtShape import MakeXmtShape

# declared kernel fields preserve exact typed ownership without saved record values
KAnalyticShapes = MappingProxyType(
    {
        29: MakeXmtShape(
            "POINT",
            "node_id:d attributes_features:p1019 owner:p1011 next:p29 previous:p29 pvec:v",
        ),
        30: MakeXmtShape(
            "LINE",
            "node_id:d attributes_features:p1019 owner:p1010 next:p1008 previous:p1008 geometric_owner:p141 sense:c pvec:v direction:v",
        ),
        31: MakeXmtShape(
            "CIRCLE",
            "node_id:d attributes_features:p1019 owner:p1010 next:p1008 previous:p1008 geometric_owner:p141 sense:c centre:v normal:v x_axis:v radius:f",
        ),
        50: MakeXmtShape(
            "PLANE",
            "node_id:d attributes_features:p1019 owner:p1007 next:p1006 previous:p1006 geometric_owner:p141 sense:c pvec:v normal:v x_axis:v",
        ),
        51: MakeXmtShape(
            "CYLINDER",
            "node_id:d attributes_features:p1019 owner:p1007 next:p1006 previous:p1006 geometric_owner:p141 sense:c pvec:v axis:v radius:f x_axis:v",
        ),
    }
)
