from __future__ import annotations

from base64 import b64decode as DecodeBytes
from hashlib import sha256 as HashBytes
from json import dumps as DumpJson
from os import getenv as ReadEnv
from pathlib import Path as FilePath
from typing import cast as CastValue


# the vendor pass needs the exact artifact from the guarded assembly construction process
def SaveAssemblyOutput(
    NameValue: str, Request: dict[str, object], Report: dict[str, object]
) -> None:
    OutputPath = ReadEnv("SwResearchOutput")
    if OutputPath is None:
        return
    OutputDir = FilePath(OutputPath) / "AssemblyCandidates" / "Empty"
    OutputDir.mkdir(parents=True, exist_ok=True)
    BlobValue = DecodeBytes(CastValue(str, Report["blob"]), validate=True)
    FileName = OutputDir / (NameValue + ".SLDASM")
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
    if FileName.with_suffix(".json").write_text(JsonEvidence) != len(JsonEvidence):
        raise RuntimeError("generated assembly candidate evidence was truncated")
