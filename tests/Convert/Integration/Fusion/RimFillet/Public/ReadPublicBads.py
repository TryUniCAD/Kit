# each family exercises a distinct full archive admission boundary through the public sdk
def ReadPublicBads() -> tuple[tuple[str, str], ...]:
    return (
        *(
            ("policy", NameValue)
            for NameValue in (
                "role",
                "unit",
                "expression",
                "owner",
                "reciprocal",
                "allocator",
                "selected_owner",
                "selected_alias",
                "selected_body",
                "radius_alias",
                "variable_mode",
                "scope_mode",
                "history_join",
                "dynamic_owner",
                "cached_radius",
                "recipe_face",
                "cache_distribution",
            )
        ),
        *(
            ("geometry", NameValue)
            for NameValue in (
                "torus_major",
                "torus_minor",
                "torus_center",
                "top_winding",
                "seam_parameter",
                "tracker_owner",
                "snapshot_height",
                "history_end",
                "history_scale",
                "selected_lower",
                "adjacent_faces",
                "body_clock",
                "blend_operation",
                "bottom_source",
                "attribute_cycle",
            )
        ),
        *(
            ("mass", FieldName + ":" + AxisName)
            for FieldName, AxisName in (
                ("volume", ""),
                ("area", ""),
                ("cog", "x"),
                ("cog", "y"),
                ("cog", "z"),
                ("moi", "x"),
                ("moi", "y"),
                ("moi", "z"),
                ("moiOffDiag", "x"),
                ("moiOffDiag", "y"),
                ("moiOffDiag", "z"),
            )
        ),
    )
