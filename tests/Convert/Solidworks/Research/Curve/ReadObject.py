from __future__ import annotations

from json import loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue


# structured process evidence must remain readable without importing the research serializer
def ReadObject(TargetPath: FilePath) -> dict[str, object]:
    return CastValue(
        dict[str, object], LoadJson(TargetPath.read_text(encoding="utf-8"))
    )
