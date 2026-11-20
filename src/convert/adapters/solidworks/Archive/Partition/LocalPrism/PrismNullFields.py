from types import MappingProxyType

# bare local cells omit optional attachments and carry no historical or attribute links
KPrismNullFields = MappingProxyType(
    {
        12: (
            "attributes_features",
            "attribute_chains",
            "lattice",
            "surface",
            "curve",
            "point",
            "mesh",
            "polyline",
            "key",
            "ref_instance",
            "next",
            "previous",
            "owner",
            "boundary_lattice",
            "boundary_mesh",
            "boundary_polyline",
            "index_map_offset",
            "index_map",
            "node_id_index_map",
            "schema_embedding_map",
            "child",
            "lowest_node_id",
            "mesh_offset_data",
        ),
        13: ("attributes_features", "next", "edge", "vertex"),
        14: ("attributes_features", "next_on_surface", "previous_on_surface"),
        15: ("attributes_features", "next"),
        16: ("attributes_features", "next_on_curve", "previous_on_curve"),
        17: ("attributes_features", "curve"),
        18: ("attributes_features",),
        19: ("attributes_features", "frame", "owner"),
        29: ("attributes_features",),
        30: ("attributes_features", "geometric_owner"),
        31: ("attributes_features", "geometric_owner"),
        50: ("attributes_features", "geometric_owner"),
        51: ("attributes_features", "geometric_owner"),
    }
)
