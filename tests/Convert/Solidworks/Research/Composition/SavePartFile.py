from __future__ import annotations

from base64 import b64decode as DecodeBytes
from hashlib import sha256 as HashBytes
from json import dumps as DumpJson
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArtifactIO.ArtifactDirs import CandidateDir
from tests.Convert.Solidworks.Research.ArtifactIO.ArtifactPaths import ArtifactFile


# native inspection needs the exact generated child and its authored inputs
def SavePartFile(
    FileName: str, Request: dict[str, object], Report: dict[str, object]
) -> None:
    OutputDir = CandidateDir("PartCandidates", "SelfReference")
    if OutputDir is None:
        return
    OutputDir.mkdir(parents=True, exist_ok=True)
    PartBytes = DecodeBytes(CastValue(str, Report["blob"]), validate=True)
    Candidate = ArtifactFile(OutputDir, FileName + ".SLDPRT")
    JsonPath = ArtifactFile(OutputDir, Candidate.with_suffix(".json").name)
    Written = Candidate.write_bytes(PartBytes)
    assert Written == len(PartBytes)
    Receipt = {
        FieldName: Value for FieldName, Value in Report.items() if FieldName != "blob"
    }
    Receipt.update(
        request=Request, bytes=len(PartBytes), sha256=HashBytes(PartBytes).hexdigest()
    )
    JsonText = DumpJson(Receipt, indent=2) + "\n"
    JsonSize = JsonPath.write_text(JsonText, encoding="utf-8")
    assert JsonSize == len(JsonText)
