from tests.Convert.Solidworks.Research.Drawing.Construction.RunCtorReject import (
    RunCtorReject,
)


# every rejected constructor contract must be exercised through the actual complete document process
def TestSheetInput() -> None:
    for ProbeName in (
        "scale_zero",
        "scale_boolean",
        "paper_format",
        "length_unit",
        "sheet_delimiter",
        "sheet_xml",
        "support_name",
        "archive_version",
        "service_pack",
        "id_domain",
        "creation_time",
        "kernel_provenance",
        "foreign_owner",
        "external_component",
    ):
        RunCtorReject(ProbeName)
