from base64 import b64decode as DecodeBytes
from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Construction.Part.RunPartPhase import (
    RunPartPhase,
)


# polygon reader evidence must originate in a separate guarded neutral construction process
def RunLineBuild(Request: dict[str, object], OutputDir: FilePath) -> FilePath:
    First = RunPartPhase(Request, "build", "polygon")
    Second = RunPartPhase(Request, "build", "polygon")
    assert First["sha256"] == Second["sha256"]
    BlobValue = DecodeBytes(CastValue(str, First["blob"]), validate=True)
    assert len(BlobValue) == First["bytes"]
    assert HashBytes(BlobValue).hexdigest() == First["sha256"]
    OutputDir.mkdir()
    OutputPath = OutputDir / "GeneratedPolygon.SLDPRT"
    with OutputPath.open("xb") as Output:
        assert Output.write(BlobValue) == len(BlobValue)
    return OutputPath
