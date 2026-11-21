from __future__ import annotations


# independently authored design inputs prevent saved native controls from supplying output values
def MakePartInput(
    Vertices: list[list[float]], DepthValue: float, NameValue: str
) -> dict[str, object]:
    return {
        "document": {
            "name": NameValue,
            "configuration_name": "authored configuration",
            "sketch_name": "Sketch1",
            "extrusion_name": "Boss-Extrude1",
            "origin_name": "Origin",
            "plane_axis": "z",
            "vertices_m": Vertices,
            "depth_m": DepthValue,
            "density_kg_m3": 1.0,
        },
        "provenance": {
            "author": "Kit research",
            "company": "authored compatibility experiment",
            "created_at": 1794700000,
            "modified_at": 1794700000,
            "comment": "generated from neutral geometry",
            "originating_build_code": 2026001,
            "license_origin": 0,
        },
        "target": {"date_code": 2026306, "parasolid_version": 370108},
        "presentation": {
            "folder_names": {
                "moCommentsFolder_c": "authored comments",
                "moFavoriteFolder_c": "authored favorites",
                "moHistoryFolder_c": "authored history",
                "moSelectionSetFolder_c": "authored selection sets",
                "moSensorFolder_c": "authored sensors",
                "moDocsFolder_c": "authored document binder",
                "moSurfaceBodyFolder_c": "authored surfaces",
                "moSolidBodyFolder_c": "authored solids",
                "moEnvFolder_c": "authored environment",
                "moNotesAreaFtrFolder_c": "authored markups",
                "moEqnFolder_c": "authored equations",
                "moMaterialFolder_c": "authored material",
            },
            "cabinet_name": "authored annotations",
            "plane_names": {"x": "Right Plane", "y": "Top Plane", "z": "Front Plane"},
            "units": {
                "length_unit": "mm",
                "angle_unit": "degree",
                "unit_system": "mmgs",
                "decimal_places": 4,
            },
            "styles": {
                "standard": 1,
                "font_name": "Arial",
                "line_style_name": "authored continuous",
                "language_id": 1033,
                "print_widths_m": [
                    0.0001,
                    0.0002,
                    0.0003,
                    0.0004,
                    0.0005,
                    0.0006,
                    0.0007,
                    0.0008,
                ],
                "exclusion_names": [],
                "task_labels": ["description", "high", "low", "complete", "reminder"],
                "cutlist_expressions": ["item", "description", "stock"],
            },
            "hatch_name": "authored hatch",
            "drafting_standard": "moISO_c",
            "journal_name": "authored journal",
            "tessellation": [20, 15, 3, False],
            "detail_flags": [],
            "system_preference_7a": False,
            "design_intent": False,
            "selected_leader": 0,
            "cjk_saved": False,
        },
    }
