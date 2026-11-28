from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Api.Fusion.DistinctFinishes.PrepareFinReq import PrepareFinReq


# a standalone folder contains only the placement request before a fresh process starts
def TextureCase(Folder: FilePath, Origin: tuple[float, float, float]) -> FilePath:
    Appearance = PrepareFinReq(Folder, 0.65)
    Retained = Folder / "Retained.f3d"
    _ = Retained.replace(Folder / "Retained.archive")
    assert not Retained.exists() and not (Folder / "Original.f3d").exists()
    Request = Appearance.parent / "Placement.json"
    Values = CastValue(
        dict[str, object], LoadJson(Appearance.read_text(encoding="utf-8"))
    )
    _ = Request.write_text(
        DumpJson(
            {
                "schema": 1,
                "scope": "fixed_cuboid_body_texture_placement",
                "appearance_request": Values,
                "wood_origin_cm": Origin,
            }
        ),
        encoding="utf-8",
    )
    _ = Appearance.replace(Folder / "Appearance.json")
    assert tuple(Request.parent.iterdir()) == (Request,)
    return Request
