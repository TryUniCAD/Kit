from base64 import b64decode as DecodeBase
from pathlib import Path as FilePath, PureWindowsPath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Assembly.Combined.RunCombinedCase import (
    RunCombinedCase,
)


# the public read boundary needs physical parent and child archives with their actual authored basenames
def WriteMateCase(FolderValue: FilePath, Request: dict[str, object]) -> FilePath:
    Report = RunCombinedCase(Request)
    Bundle = CastValue(dict[str, object], Request["bundle"])
    FolderValue.mkdir()
    Files: list[FilePath] = []
    for RoleName in ("assembly", "child"):
        Document = CastValue(dict[str, object], Bundle[RoleName])
        OutputValue = CastValue(dict[str, str], Document["output"])
        ReportData = CastValue(dict[str, str], Report[RoleName])
        FileValue = FolderValue / PureWindowsPath(OutputValue["path_name"]).name
        _ = FileValue.write_bytes(
            DecodeBase(ReportData["artifact_base64"], validate=True)
        )
        Files.append(FileValue)
    return Files[0]
