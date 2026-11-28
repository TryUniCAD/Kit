from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasNum import ReadMeasNum
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# receipt tree rows must be clear and retain the actual generated shape owners
def CheckCircTree(Stage: dict[str, object], PlanValue: CirclePlan) -> None:
    TreeValue = ReadMeasRows(Stage.get("top_level_features"), 19)
    if len(TreeValue) != 19 or any(
        type(RowValue.get("error")) is not int
        or RowValue["error"] != 0
        or RowValue.get("warning") is not False
        or RowValue.get("suppressed") is not False
        for RowValue in TreeValue
    ):
        raise ValueError("circle measured feature tree did not rebuild cleanly")
    if tuple(
        (RowValue.get("name"), RowValue.get("type")) for RowValue in TreeValue[-2:]
    ) != (
        (PlanValue.SketchName, "ProfileFeature"),
        (PlanValue.FeatureName, "Extrusion"),
    ):
        raise ValueError(
            "circle native feature evidence has a different sketch or boss"
        )


# each stage must open the actual preceding artifact and produce its owned clean save
def CheckCircStage(
    Stage: dict[str, object], NameValue: str, SourceSha: str, PlanValue: CirclePlan
) -> str:
    if (
        Stage.get("phase") != NameValue
        or Stage.get("source_sha256") != SourceSha
        or type(Stage.get("open_errors")) is not int
        or Stage["open_errors"] != 0
        or type(Stage.get("open_warnings")) is not int
        or Stage["open_warnings"] != 0
        or type(Stage.get("initial_body_count")) is not int
        or Stage["initial_body_count"] != 1
        or ReadMeasNum(Stage.get("numeric_checks")) < 20
        or type(Stage.get("saved_bytes")) is not int
        or ReadMeasNum(Stage["saved_bytes"]) < 1
    ):
        raise ValueError("circle native staged open or saved identity does not qualify")
    CheckCircTree(Stage, PlanValue)
    _ = ReadMeasSha(Stage.get("record_sha256"))
    return ReadMeasSha(Stage.get("saved_sha256"))
