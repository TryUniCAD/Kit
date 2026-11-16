from __future__ import annotations

from base64 import b64decode as DecodeBytes
from hashlib import sha256 as HashBytes
from json import dumps as DumpJson
from os import getenv as ReadEnv
from pathlib import Path as FilePath
from typing import cast as CastValue


# remote artifacts preserve exact generated files for independent native application inspection
def SavePartOutput(
    NameValue: str, Request: dict[str, object], Report: dict[str, object]
) -> None:
    OutputPath = ReadEnv("SwResearchOutput")
    if OutputPath is None:
        return
    OutputDir = FilePath(OutputPath)
    OutputDir.mkdir(parents=True, exist_ok=True)
    BlobValue = DecodeBytes(CastValue(str, Report["blob"]), validate=True)
    FileName = OutputDir / (NameValue + ".SLDPRT")
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
    WrittenChars = FileName.with_suffix(".json").write_text(JsonEvidence)
    if WrittenChars != len(JsonEvidence):
        raise RuntimeError("generated candidate evidence was truncated")
