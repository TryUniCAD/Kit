from base64 import b64decode as DecodeBytes
from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Construction.RectangleAnchors.RunCornerPhase import (
    RunCornerPhase,
)


# public origin evidence starts with two isolated deterministic neutral builds rather than a saved native seed
def RunOriginBuild(RequestValue: dict[str, object], OutputDir: FilePath) -> FilePath:
    FirstValue = RunCornerPhase(RequestValue, "build")
    SecondValue = RunCornerPhase(RequestValue, "build")
    assert FirstValue["sha256"] == SecondValue["sha256"]
    BlobValue = DecodeBytes(CastValue(str, FirstValue["blob"]), validate=True)
    assert len(BlobValue) == FirstValue["bytes"]
    assert HashBytes(BlobValue).hexdigest() == FirstValue["sha256"]
    OutputDir.mkdir()
    OutputPath = OutputDir / "GeneratedOrigin.SLDPRT"
    with OutputPath.open("xb") as Output:
        WrittenSize = Output.write(BlobValue)
        assert WrittenSize == len(BlobValue)
    return OutputPath
