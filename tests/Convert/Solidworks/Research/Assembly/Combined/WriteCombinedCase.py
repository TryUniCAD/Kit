from base64 import b64decode as Decode64
from pathlib import Path as FilePath, PureWindowsPath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Assembly.Combined.RunCombinedCase import (
    RunCombinedCase,
)


# the public read boundary needs physical parent and child archives with their actual authored basenames
def WriteCombinedCase(FolderValue: FilePath, Request: dict[str, object]) -> FilePath:
    Report = RunCombinedCase(Request)
    Bundle = CastValue(dict[str, object], Request["bundle"])
    FolderValue.mkdir()
    Files: list[FilePath] = []
    for Role in ("assembly", "child"):
        Document = CastValue(dict[str, object], Bundle[Role])
        OutputValue = CastValue(dict[str, str], Document["output"])
        Data = CastValue(dict[str, str], Report[Role])
        FileValue = FolderValue / PureWindowsPath(OutputValue["path_name"]).name
        _ = FileValue.write_bytes(Decode64(Data["artifact_base64"], validate=True))
        Files.append(FileValue)
    return Files[0]
