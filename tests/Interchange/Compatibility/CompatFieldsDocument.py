# historical document fields stay isolated so dataclass reflection expectations remain reviewable
KCompatFieldsDocument = (
    (
        "interchange.document.CadDocument",
        (
            "source",
            "configurations",
            "parameters",
            "support_planes",
            "sketches",
            "selections",
            "feature_timeline",
            "bodies",
            "meshes",
            "brep_payloads",
            "diagnostics",
            "capabilities",
            "metadata",
            "units",
            "schema_version",
            "assembly",
            "brep",
            "materials",
            "drawing",
        ),
    ),
    (
        "interchange.document.DrawingData",
        ("active_sheet_id", "sheets", "model_refs"),
    ),
    (
        "interchange.document.DrawingModelRef",
        ("id", "source_path", "source_format_id"),
    ),
    (
        "interchange.document.DrawingSheet",
        ("id", "name", "width", "height", "scale_ratio", "views", "notes"),
    ),
    (
        "interchange.document.DrawingView",
        (
            "id",
            "name",
            "model_ref_id",
            "configuration_name",
            "position",
            "orientation_name",
            "scale_ratio",
            "model_to_sheet",
            "outline",
        ),
    ),
)
