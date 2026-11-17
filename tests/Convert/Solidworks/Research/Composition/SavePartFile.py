from __future__ import annotations

from base64 import b64decode as DecodeBytes
from hashlib import sha256 as HashBytes
from json import dumps as DumpJson
from os import getenv as ReadEnv
from pathlib import Path as FilePath
from typing import cast as CastValue


# native inspection needs the exact generated child and its authored inputs
def SavePartFile(
    FileName: str, Request: dict[str, object], Report: dict[str, object]
) -> None:
    OutputPath = ReadEnv("SwResearchOutput")
    if OutputPath is None:
        return
    OutputDir = FilePath(OutputPath) / "PartCandidates" / "SelfReference"
    OutputDir.mkdir(parents=True, exist_ok=True)
    PartBytes = DecodeBytes(CastValue(str, Report["blob"]), validate=True)
    Candidate = OutputDir / (FileName + ".SLDPRT")
    assert Candidate.write_bytes(PartBytes) == len(PartBytes)
    Receipt = {
        FieldName: Value for FieldName, Value in Report.items() if FieldName != "blob"
    }
    Receipt.update(
        request=Request, bytes=len(PartBytes), sha256=HashBytes(PartBytes).hexdigest()
    )
    JsonText = DumpJson(Receipt, indent=2) + "\n"
    assert Candidate.with_suffix(".json").write_text(JsonText, encoding="utf-8") == len(
        JsonText
    )
