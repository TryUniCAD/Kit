from __future__ import annotations

from base64 import b64decode as DecodeBytes
from hashlib import sha256 as HashBytes
from json import dumps as DumpJson
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArtifactIO.ArtifactDirs import CandidateDir
from tests.Convert.Solidworks.Research.ArtifactIO.ArtifactPaths import ArtifactFile


# the vendor needs the generated assembly and its generated child together
def SaveOccBundle(
    NameValue: str, Request: dict[str, object], Report: dict[str, object]
) -> None:
    OutputDir = CandidateDir("AssemblyOccurrences", NameValue)
    if OutputDir is None:
        return
    OutputDir.mkdir(parents=True, exist_ok=True)
    Child = CastValue(dict[str, object], Report["child"])
    AssemblyBlob = DecodeBytes(CastValue(str, Report["blob"]), validate=True)
    ChildBlob = DecodeBytes(CastValue(str, Child["blob"]), validate=True)
    ParentFile = ArtifactFile(OutputDir, NameValue + ".SLDASM")
    ChildFile = ArtifactFile(OutputDir, "GeneratedChildFile.SLDPRT")
    ReceiptPath = ArtifactFile(OutputDir, "receipt.json")
    ParentSize = ParentFile.write_bytes(AssemblyBlob)
    ChildSize = ChildFile.write_bytes(ChildBlob)
    assert ParentSize == len(AssemblyBlob) and ChildSize == len(ChildBlob)
    Receipt = {
        KeyValue: Value for KeyValue, Value in Report.items() if KeyValue != "blob"
    }
    Receipt.update(
        request=Request,
        assembly_sha256=HashBytes(AssemblyBlob).hexdigest(),
        child={
            KeyValue: Value for KeyValue, Value in Child.items() if KeyValue != "blob"
        },
    )
    TextValue = DumpJson(Receipt, indent=2) + "\n"
    Written = ReceiptPath.write_text(TextValue, encoding="utf-8")
    assert Written == len(TextValue)
