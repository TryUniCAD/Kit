from types import MappingProxyType

from convert.adapters.solidworks.Archive.Partition.MakeXmtShape import MakeXmtShape

# declared kernel fields preserve exact typed ownership without saved record values
KAttributeShapes = MappingProxyType(
    {
        70: MakeXmtShape(
            "LIST",
            "node_id:d owner:p1013 next:p70 previous:p70 list_type:d list_length:d block_length:d size_of_entry:d list_block:p1012 finger_block:p1012 finger_index:d notransmit:l",
            "node_id:d list_type:u notransmit:l owner:p1013 next:p70 previous:p70 list_length:d block_length:d finger_index:d finger_block:p1012 list_block:p1012",
        ),
        74: MakeXmtShape(
            "POINTER_LIS_BLOCK",
            "n_entries:d next_block:p74 entries:p1001*1",
            "n_entries:d index_map_offset:d next_block:p74 entries:p1001*1",
        ),
        79: MakeXmtShape("ATT_DEF_ID", "string:c*1"),
        80: MakeXmtShape(
            "ATTRIB_DEF",
            "next:p80 identifier:p79 type_id:d actions:u*8 field_names:p99 legal_owners:l*14 fields:u*1",
            "next:p80 identifier:p79 type_id:d actions:u*8 field_names:p99 legal_owners:l*17 fields:u*1",
        ),
        81: MakeXmtShape(
            "ATTRIBUTE",
            "node_id:d definition:p80 owner:p1015 next:p1019 previous:p1019 next_of_type:p81 previous_of_type:p81 fields:p1018*1",
        ),
        82: MakeXmtShape("INT_VALUES", "values:d*1"),
        83: MakeXmtShape("REAL_VALUES", "values:f*1"),
        84: MakeXmtShape("CHAR_VALUES", "values:c*1"),
        98: MakeXmtShape("UNICODE_VALUES", "values:w*1"),
    }
)
