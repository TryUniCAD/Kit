from __future__ import annotations

from base64 import b64decode as DecodeBytes
from hashlib import sha256 as HashBytes
from json import dumps as DumpJson
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArtifactIO.ArtifactDirs import CandidateDir
from tests.Convert.Solidworks.Research.ArtifactIO.ArtifactPaths import ArtifactFile


# the vendor pass needs the exact artifact from the guarded assembly construction process
def SaveCandidate(
    NameValue: str, Request: dict[str, object], Report: dict[str, object]
) -> None:
    OutputDir = CandidateDir("AssemblyCandidates", "Empty")
    if OutputDir is None:
        return
    OutputDir.mkdir(parents=True, exist_ok=True)
    BlobValue = DecodeBytes(CastValue(str, Report["blob"]), validate=True)
    FileName = ArtifactFile(OutputDir, NameValue + ".SLDASM")
    JsonPath = ArtifactFile(OutputDir, FileName.with_suffix(".json").name)
    if FileName.write_bytes(BlobValue) != len(BlobValue):
        raise RuntimeError("generated assembly candidate artifact was truncated")
    Evidence = {
        KeyName: Value for KeyName, Value in Report.items() if KeyName != "blob"
    }
    Evidence.update(
        {
            "sha256": HashBytes(BlobValue).hexdigest(),
            "bytes": len(BlobValue),
            "request": Request,
            "source_policy": "authored empty assembly only; no native source streams",
        }
    )
    JsonEvidence = DumpJson(Evidence, indent=2) + "\n"
    if JsonPath.write_text(JsonEvidence) != len(JsonEvidence):
        raise RuntimeError("generated assembly candidate evidence was truncated")
