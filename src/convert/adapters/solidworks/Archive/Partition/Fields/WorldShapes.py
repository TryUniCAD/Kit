from types import MappingProxyType

from convert.adapters.solidworks.Archive.Partition.MakeXmtShape import MakeXmtShape

# declared kernel fields preserve exact typed ownership without saved record values
KWorldShapes = MappingProxyType(
    {
        3: MakeXmtShape("PARTITION", "current_pmark:p4 highest_id:d"),
        4: MakeXmtShape(
            "PMARK",
            "preceding:p4 first_following:p4 next_sibling:p4 prev_sibling:p4 n_new_nodes:d n_del_nodes:d n_copy_mod_nodes:d delta_key:d delta_is_forward:l id:d",
        ),
        101: MakeXmtShape(
            "WORLD",
            "assembly:p10 attribute:p81 body:p12 transform:p100 surface:p1006 curve:p1008 point:p29 alive:l attrib_def:p80 highest_id:d current_id:d",
            "assembly:p10 attribute:p81 body:p12 transform:p100 surface:p1006 curve:p1008 point:p29 mesh:p1006 polyline:p1008 lattice:p222 alive:l attrib_def:p80 attdef_list:p74 highest_id:d current_id:d index_map_offset:d index_map:p82 schema_embedding_map:p82 mesh_offset_data:p206",
        ),
    }
)
