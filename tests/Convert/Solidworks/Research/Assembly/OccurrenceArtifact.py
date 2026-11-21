from __future__ import annotations

from base64 import b64decode as DecodeBytes
from hashlib import sha256 as HashBytes
from json import dumps as DumpJson
from os import getenv as ReadEnv
from pathlib import Path as FilePath
from typing import cast as CastValue


# the vendor needs the generated assembly and its generated child together
def SaveOccBundle(
    NameValue: str, Request: dict[str, object], Report: dict[str, object]
) -> None:
    OutputPath = ReadEnv("SwResearchOutput")
    if OutputPath is None:
        return
    OutputDir = FilePath(OutputPath) / "AssemblyOccurrences" / NameValue
    OutputDir.mkdir(parents=True, exist_ok=True)
    Child = CastValue(dict[str, object], Report["child"])
    AssemblyBlob = DecodeBytes(CastValue(str, Report["blob"]), validate=True)
    ChildBlob = DecodeBytes(CastValue(str, Child["blob"]), validate=True)
    assert (OutputDir / (NameValue + ".SLDASM")).write_bytes(AssemblyBlob) == len(
        AssemblyBlob
    )
    assert (OutputDir / "GeneratedChildFile.SLDPRT").write_bytes(ChildBlob) == len(
        ChildBlob
    )
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
    assert (OutputDir / "receipt.json").write_text(TextValue, encoding="utf-8") == len(
        TextValue
    )
