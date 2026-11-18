from base64 import b64decode as DecodeBytes
from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Construction.RectDimensions.RunRectDimPhase import (
    RunRectDimPhase,
)


# typed dimension reader evidence must begin with independently guarded neutral construction and unchanged complete archive bytes
def RunDimBuild(RequestValue: dict[str, object], OutputDir: FilePath) -> FilePath:
    FirstValue = RunRectDimPhase(RequestValue, "build")
    SecondValue = RunRectDimPhase(RequestValue, "build")
    assert FirstValue["sha256"] == SecondValue["sha256"]
    BlobValue = DecodeBytes(CastValue(str, FirstValue["blob"]), validate=True)
    assert len(BlobValue) == FirstValue["bytes"]
    assert HashBytes(BlobValue).hexdigest() == FirstValue["sha256"]
    OutputDir.mkdir()
    OutputPath = OutputDir / "GeneratedDimensions.SLDPRT"
    with OutputPath.open("xb") as Output:
        assert Output.write(BlobValue) == len(BlobValue)
    return OutputPath
