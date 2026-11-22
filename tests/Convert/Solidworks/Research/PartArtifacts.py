from __future__ import annotations

from base64 import b64decode as DecodeBytes
from hashlib import sha256 as HashBytes
from json import dumps as DumpJson
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArtifactIO.ArtifactDirs import CandidateDir
from tests.Convert.Solidworks.Research.ArtifactIO.ArtifactPaths import ArtifactFile


# remote artifacts preserve exact generated files for independent native application inspection
def SavePartOutput(
    NameValue: str, Request: dict[str, object], Report: dict[str, object]
) -> None:
    OutputDir = CandidateDir()
    if OutputDir is None:
        return
    OutputDir.mkdir(parents=True, exist_ok=True)
    BlobValue = DecodeBytes(CastValue(str, Report["blob"]), validate=True)
    FileName = ArtifactFile(OutputDir, NameValue + ".SLDPRT")
    JsonPath = ArtifactFile(OutputDir, FileName.with_suffix(".json").name)
    WrittenBytes = FileName.write_bytes(BlobValue)
    if WrittenBytes != len(BlobValue):
        raise RuntimeError("generated candidate artifact was truncated")
    Evidence = {
        KeyValue: Value for KeyValue, Value in Report.items() if KeyValue != "blob"
    }
    Evidence.update(
        {
            "sha256": HashBytes(BlobValue).hexdigest(),
            "bytes": len(BlobValue),
            "request": Request,
            "source_policy": "neutral authored geometry only; no native source streams",
        }
    )
    JsonEvidence = DumpJson(Evidence, indent=2) + "\n"
    WrittenChars = JsonPath.write_text(JsonEvidence)
    if WrittenChars != len(JsonEvidence):
        raise RuntimeError("generated candidate evidence was truncated")
