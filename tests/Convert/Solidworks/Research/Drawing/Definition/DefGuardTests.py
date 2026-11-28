from tests.Convert.Solidworks.Research.Drawing.Definition.RunDefReject import (
    RunDefReject,
)


# every deliberately unsupported owner must reject the complete guarded document process
def TestDefGuards() -> None:
    for ProbeName in (
        "archive_version",
        "runtime_schema",
        "drawing_root",
        "populated_links",
        "sheet_format",
        "sheet_alias",
        "material_payload",
        "trailer_marker",
        "layer_mask",
        "detail_bucket",
        "sketch_rows",
        "sheet_presence",
    ):
        RunDefReject(ProbeName)
