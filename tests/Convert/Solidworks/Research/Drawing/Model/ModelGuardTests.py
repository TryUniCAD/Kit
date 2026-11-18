from tests.Convert.Solidworks.Research.Drawing.Model.MakeModelInput import (
    MakeModelInput,
)
from tests.Convert.Solidworks.Research.Drawing.Model.RunModelReject import (
    RunModelReject,
)


# invalid presentation provenance and graph contracts must reject without producing a partial model artifact
def TestModelGuards() -> None:
    Request = MakeModelInput("ModelReject", 11, 3)
    for ProbeName in (
        "model_name",
        "folder_name",
        "folder_contract",
        "sheet_scale",
        "sheet_format",
        "sheet_unit",
        "creation_time",
        "block_identity",
        "block_type",
        "dimension_link",
        "style_contract",
        "style_standard",
        "style_tasks",
        "style_font",
        "unit_contract",
        "target_contract",
        "service_pack",
        "build_contract",
    ):
        RunModelReject(Request, ProbeName)
