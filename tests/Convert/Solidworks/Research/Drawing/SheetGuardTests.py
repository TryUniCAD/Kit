from tests.Convert.Solidworks.Research.Drawing.RunSheetReject import RunSheetReject


# complete drawing jobs must reject every unproved sheet boundary without silent field loss
def TestSheetGuards() -> None:
    for ProbeName in (
        "archive_version",
        "archive_conditions",
        "runtime_schema",
        "annotation_presence",
        "annotation_marker",
        "ink_view",
        "missing_presence",
    ):
        RunSheetReject(ProbeName)
