from __future__ import annotations

from typing import cast as CastValue

from tests.convert.solidworks.research.FreshPartInput import MakePartInput


def LockedPartInput(RecordData: dict[str, object]) -> dict[str, object]:
    ModelSpec = CastValue(dict[str, object], RecordData["spec"])
    Features = CastValue(list[dict[str, object]], ModelSpec["ops"])
    Entities = CastValue(list[dict[str, object]], Features[0]["entities"])
    Vertices = [
        [Value / 1000 for Value in CastValue(list[float], Entity["p"])[:2]]
        for Entity in Entities
    ]
    return MakePartInput(
        Vertices,
        CastValue(float, Features[1]["depth"]) / 1000,
        CastValue(str, ModelSpec["name"]),
    )
