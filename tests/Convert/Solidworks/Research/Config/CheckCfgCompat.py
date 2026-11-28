from pathlib import Path as FilePath
from typing import cast as CastValue

from convert import open_document as OpenDocument
from tests.Convert.Solidworks.Research.ArchiveProcess import RunArchive
from tests.Convert.Solidworks.Research.Config.MakeConfigTail import MakeConfigTail
from tests.Convert.Solidworks.Research.Config.RunConfigTool import RunConfigTool
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject


# research compatibility cannot confer complete sdk admission on a configuration with unread data
def CheckCfgCompat(InputPath: FilePath) -> None:
    OutputPath = MakeConfigTail(InputPath)
    RejectedPath = OutputPath.with_suffix(".sdk.json")
    Rejected = RunConfigTool("CheckSdkConfig.py", (OutputPath,), RejectedPath)
    assert (
        Rejected.returncode != 0
        and "trailing bytes" in Rejected.stderr
        and not RejectedPath.exists()
    )
    ReportPath = OutputPath.with_suffix(".research.json")
    Outcome = RunArchive(
        str(OutputPath),
        "Contents/Config-0",
        ("--require-proven", "--report", str(ReportPath)),
    )
    assert Outcome.returncode != 0
    Report = ReadObject(ReportPath)
    assert Report["passed"] is False and Report["proven_schemas"] is False
    (FileValue,) = CastValue(list[dict[str, object]], Report["files"])
    Streams = CastValue(dict[str, dict[str, object]], FileValue["streams"])
    StreamValue = Streams["Contents/Config-0"]
    assert StreamValue["tail"] == 2 and StreamValue["identical"] is True
    UsageValue = CastValue(dict[str, dict[str, object]], StreamValue["schema_usage"])
    for Direction in ("load", "store"):
        Shared = CastValue(
            list[dict[str, object]], UsageValue[Direction]["shared_schema_usage"]
        )
        assert all(
            RowValue["admitted"] is False
            for RowValue in Shared
            if RowValue["codec"] == "sdk_ordinary_config"
        )
    Document = OpenDocument(OutputPath, include_brep=False, include_tessellation=False)
    InfoValue = CastValue(
        dict[str, object], Document.metadata["solidworks.typed_configuration_graph"]
    )
    assert (
        InfoValue["status"] == "unsupported" and InfoValue["full_linked_graph"] is False
    )
    assert any(
        RowValue.code == "solidworks.typed_configuration_graph_unavailable"
        for RowValue in Document.diagnostics
    )
