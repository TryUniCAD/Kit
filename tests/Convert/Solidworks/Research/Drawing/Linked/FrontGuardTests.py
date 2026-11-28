from tests.Convert.Solidworks.Research.Drawing.Linked.MakeFrontJob import MakeFrontJob
from tests.Convert.Solidworks.Research.Drawing.Linked.RunFrontReject import (
    RunFrontReject,
)


# each unsupported ownership context must remain an explicit process rejection instead of broadening blank or linked coverage
def TestFrontGuards() -> None:
    JobValue = MakeFrontJob("LinkedReject", 0.0293, 0.0221, 0.0107)
    for ProbeName in (
        "archive_version",
        "orientation",
        "view_scale",
        "view_rotation",
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
    ):
        RunFrontReject(JobValue, ProbeName)
