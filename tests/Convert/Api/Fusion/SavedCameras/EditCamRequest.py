from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue


# a reordered request with one changed position distinguishes regeneration from unchanged replay
def EditCamRequest(Request: FilePath) -> None:
    Handoff = CastValue(
        dict[str, object], LoadJson(Request.read_text(encoding="utf-8"))
    )
    Views = CastValue(list[dict[str, object]], Handoff["named_views"])
    Camera = CastValue(dict[str, object], Views[-1]["camera"])
    Position = CastValue(list[float], Camera["position"])
    Position[0] += 0.25
    Views.reverse()
    _ = Request.write_text(DumpJson(Handoff), encoding="utf-8")
