from base64 import b64decode as DecodeBytes
from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Construction.Part.RunPartPhase import (
    RunPartPhase,
)


# presentation integration must consume fresh sdk constructed containers with the existing input read and research import guards
def RunTreeBuild(Request: dict[str, object], OutputDir: FilePath) -> FilePath:
    Report = RunPartPhase(Request, "build")
    BlobValue = DecodeBytes(CastValue(str, Report["blob"]), validate=True)
    assert len(BlobValue) == Report["bytes"]
    assert HashBytes(BlobValue).hexdigest() == Report["sha256"]
    OutputDir.mkdir()
    OutputPath = OutputDir / "GeneratedChildFile.SLDPRT"
    with OutputPath.open("xb") as Output:
        assert Output.write(BlobValue) == len(BlobValue)
    return OutputPath
