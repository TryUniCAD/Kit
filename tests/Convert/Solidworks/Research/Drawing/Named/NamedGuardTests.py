from tests.Convert.Solidworks.Research.Drawing.Named.MakeNamedJob import MakeNamedJob
from tests.Convert.Solidworks.Research.Drawing.Named.RunNamedReject import (
    RunNamedReject,
)


# named admission must preserve the original ownership exclusions and reject invalid explicit scale states
def TestNamedGuards() -> None:
    JobValue = MakeNamedJob(
        "NamedReject", "*Top", 0.9375, 0.0277, 0.0203, 0.0119, 0.13917, 0.09683
    )
    for ProbeName in (
        "archive_version",
        "view_owner",
        "active_sheet",
        "directory_alias",
        "property_alias",
        "property_config",
        "external_backlink",
        "external_name",
        "external_owner",
        "support_alias",
        "support_owner",
        "annotation",
        "view_cache",
        "root_preview",
        "ui_profile",
        "view_schema",
        "second_view",
        "read_tail",
        "read_version",
        "unsupported_family",
        "family_mismatch",
        "scale_zero",
        "scale_negative",
        "scale_boolean",
        "scale_nonfinite",
        "scale_underflow",
        "scale_overflow",
        "scale_frame",
        "inherited_scale",
        "read_family",
    ):
        RunNamedReject(JobValue, ProbeName)
