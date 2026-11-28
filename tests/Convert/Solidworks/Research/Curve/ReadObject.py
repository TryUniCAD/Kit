from __future__ import annotations

from json import loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArtifactIO.ArtifactPaths import CheckArtifact


# structured process evidence must remain readable without importing the research serializer
def ReadObject(TargetPath: FilePath) -> dict[str, object]:
    InputPath = CheckArtifact(TargetPath, True)
    JsonValue: object = LoadJson(InputPath.read_text(encoding="utf-8"))
    if not isinstance(JsonValue, dict):
        raise ValueError("research evidence must be a JSON object")
    return CastValue(dict[str, object], JsonValue)
