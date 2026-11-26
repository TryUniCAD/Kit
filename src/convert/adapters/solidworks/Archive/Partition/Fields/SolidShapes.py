from types import MappingProxyType

from convert.adapters.solidworks.Archive.Partition.MakeXmtShape import MakeXmtShape

# declared kernel fields preserve exact typed ownership without saved record values
KSolidShapes = MappingProxyType(
    {
        12: MakeXmtShape(
            "BODY",
            "highest_node_id:d attributes_features:p1019 attribute_chains:p70 surface:p1006 curve:p1008 point:p29 key:p102 res_size:f res_linear:f ref_instance:p11 next:p12 previous:p12 state:u owner:p101 body_type:u nom_geom_state:u shell:p13 boundary_surface:p1006 boundary_curve:p1008 boundary_point:p29 region:p19 edge:p16 vertex:p18",
            "highest_node_id:d attributes_features:p1019 attribute_chains:p70 lattice:p222 surface:p1006 curve:p1008 point:p29 mesh:p1006 polyline:p1008 key:p102 res_size:f res_linear:f ref_instance:p11 next:p12 previous:p12 state:u owner:p1040 body_type:u nom_geom_state:u shell:p13 boundary_lattice:p222 boundary_surface:p1006 boundary_curve:p1008 boundary_point:p29 boundary_mesh:p1006 boundary_polyline:p1008 region:p19 edge:p16 vertex:p18 index_map_offset:d index_map:p82 node_id_index_map:p82 schema_embedding_map:p82 child:p12 lowest_node_id:d mesh_offset_data:p206",
        ),
        13: MakeXmtShape(
            "SHELL",
            "node_id:d attributes_features:p1019 body:p12 next:p13 face:p14 edge:p16 vertex:p18 region:p19 front_face:p14",
        ),
        19: MakeXmtShape(
            "REGION",
            "node_id:d attributes_features:p1019 body:p12 next:p19 previous:p19 shell:p13 type:c",
            "node_id:d attributes_features:p1019 body:p12 next:p19 previous:p19 shell:p13 frame:p230 type:c owner:p12",
        ),
    }
)
