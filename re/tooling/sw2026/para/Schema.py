from dataclasses import dataclass
from struct import pack

from builders.EmptyPartition import BASE_WORLD, PARTITION, PMARK, WORLD, short_string
from convert.Geometry.Parasolid import WritePointerMut


@dataclass(frozen=True)
class Field:
    name: str
    encoding: str
    pointer_class: int = 0
    count: int = 0

    def descriptor(self, result):
        short_string(result, self.name)
        result.extend(pack(">H", self.pointer_class))
        WritePointerMut(result, self.count)
        if not self.pointer_class:
            short_string(result, self.encoding)
        if self.count == 1:
            result.append(1)


@dataclass(frozen=True)
class Schema:
    name: str
    base: tuple[Field, ...]
    current: tuple[Field, ...]


def fields(specification):
    result = []
    for label in specification.split():
        name, encoding = label.split(":")
        encoding, _, count = encoding.partition("*")
        pointer_class = int(encoding[1:]) if encoding.startswith("p") else 0
        result.append(Field(name, "p" if pointer_class else encoding, pointer_class, int(count or 0)))
    return tuple(result)


def shared_fields(description):
    return tuple(Field(field.name, field.encoding, field.pointer_class) for field in description)


def schema(name, base, current=None):
    return Schema(name, fields(base), fields(current if current is not None else base))


SCHEMAS = {
    3: Schema("PARTITION", shared_fields(PARTITION), shared_fields(PARTITION)),
    4: Schema("PMARK", shared_fields(PMARK), shared_fields(PMARK)),
    12: schema(
        "BODY",
        """
        highest_node_id:d attributes_features:p1019 attribute_chains:p70 surface:p1006
        curve:p1008 point:p29 key:p102 res_size:f res_linear:f ref_instance:p11 next:p12
        previous:p12 state:u owner:p101 body_type:u nom_geom_state:u shell:p13
        boundary_surface:p1006 boundary_curve:p1008 boundary_point:p29 region:p19 edge:p16 vertex:p18
        """,
        """
        highest_node_id:d attributes_features:p1019 attribute_chains:p70 lattice:p222
        surface:p1006 curve:p1008 point:p29 mesh:p1006 polyline:p1008 key:p102 res_size:f
        res_linear:f ref_instance:p11 next:p12 previous:p12 state:u owner:p1040 body_type:u
        nom_geom_state:u shell:p13 boundary_lattice:p222 boundary_surface:p1006
        boundary_curve:p1008 boundary_point:p29 boundary_mesh:p1006 boundary_polyline:p1008
        region:p19 edge:p16 vertex:p18 index_map_offset:d index_map:p82 node_id_index_map:p82
        schema_embedding_map:p82 child:p12 lowest_node_id:d mesh_offset_data:p206
        """,
    ),
    13: schema("SHELL", "node_id:d attributes_features:p1019 body:p12 next:p13 face:p14 edge:p16 vertex:p18 region:p19 front_face:p14"),
    14: schema(
        "FACE",
        """
        node_id:d attributes_features:p1019 tolerance:f next:p14 previous:p14 loop:p15
        shell:p13 surface:p1006 sense:c next_on_surface:p14 previous_on_surface:p14
        next_front:p14 previous_front:p14 front_shell:p13
        """,
    ),
    15: schema("LOOP", "node_id:d attributes_features:p1019 halfedge:p17 face:p14 next:p15"),
    16: schema(
        "EDGE",
        """
        node_id:d attributes_features:p1019 tolerance:f halfedge:p17 previous:p16 next:p16
        curve:p1008 next_on_curve:p16 previous_on_curve:p16 owner:p1029
        """,
    ),
    17: schema(
        "HALFEDGE",
        """
        attributes_features:p1019 loop:p15 forward:p17 backward:p17 vertex:p18
        other:p17 edge:p16 curve:p1008 next_at_vx:p17 sense:c
        """,
    ),
    18: schema("VERTEX", "node_id:d attributes_features:p1019 halfedge:p17 previous:p18 next:p18 point:p29 tolerance:f owner:p1029"),
    19: schema(
        "REGION",
        "node_id:d attributes_features:p1019 body:p12 next:p19 previous:p19 shell:p13 type:c",
        "node_id:d attributes_features:p1019 body:p12 next:p19 previous:p19 shell:p13 frame:p230 type:c owner:p12",
    ),
    29: schema("POINT", "node_id:d attributes_features:p1019 owner:p1011 next:p29 previous:p29 pvec:v"),
    30: schema(
        "LINE",
        "node_id:d attributes_features:p1019 owner:p1010 next:p1008 previous:p1008 geometric_owner:p141 sense:c pvec:v direction:v",
    ),
    50: schema(
        "PLANE",
        "node_id:d attributes_features:p1019 owner:p1007 next:p1006 previous:p1006 geometric_owner:p141 sense:c pvec:v normal:v x_axis:v",
    ),
    70: schema(
        "LIST",
        """
        node_id:d owner:p1013 next:p70 previous:p70 list_type:d list_length:d block_length:d
        size_of_entry:d list_block:p1012 finger_block:p1012 finger_index:d notransmit:l
        """,
        """
        node_id:d list_type:u notransmit:l owner:p1013 next:p70 previous:p70 list_length:d
        block_length:d finger_index:d finger_block:p1012 list_block:p1012
        """,
    ),
    74: schema(
        "POINTER_LIS_BLOCK",
        "n_entries:d next_block:p74 entries:p1001*1",
        "n_entries:d index_map_offset:d next_block:p74 entries:p1001*1",
    ),
    79: schema("ATT_DEF_ID", "string:c*1"),
    80: schema(
        "ATTRIB_DEF",
        "next:p80 identifier:p79 type_id:d actions:u*8 field_names:p99 legal_owners:l*14 fields:u*1",
        "next:p80 identifier:p79 type_id:d actions:u*8 field_names:p99 legal_owners:l*17 fields:u*1",
    ),
    81: schema(
        "ATTRIBUTE",
        """
        node_id:d definition:p80 owner:p1015 next:p1019 previous:p1019
        next_of_type:p81 previous_of_type:p81 fields:p1018*1
        """,
    ),
    82: schema("INT_VALUES", "values:d*1"),
    83: schema("REAL_VALUES", "values:f*1"),
    84: schema("CHAR_VALUES", "values:c*1"),
    98: schema("UNICODE_VALUES", "values:w*1"),
    101: Schema("WORLD", shared_fields(BASE_WORLD), shared_fields(WORLD)),
}
