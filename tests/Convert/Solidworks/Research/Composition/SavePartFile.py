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
    Blob = DecodeBytes(CastValue(str, Report["blob"]), validate=True)
    Candidate = OutputDir / (FileName + ".SLDPRT")
    assert Candidate.write_bytes(Blob) == len(Blob)
    Receipt = {Key: Value for Key, Value in Report.items() if Key != "blob"}
    Receipt.update(request=Request, bytes=len(Blob), sha256=HashBytes(Blob).hexdigest())
    Text = DumpJson(Receipt, indent=2) + "\n"
    assert Candidate.with_suffix(".json").write_text(Text, encoding="utf-8") == len(
        Text
    )
