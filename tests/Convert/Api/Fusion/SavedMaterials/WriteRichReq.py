from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Api.Fusion.SavedMaterials.RichMatInputs import KRichBasic, KRichMetal


# the authored wrapper must carry the new material without modifying the saved shape semantics
def WriteRichReq(BasePath: FilePath, Request: FilePath, IsMetal: bool) -> None:
    Config = CastValue(
        dict[str, object], LoadJson(BasePath.read_text(encoding="utf-8"))
    )
    Camera = CastValue(dict[str, object], Config["camera_request"])
    Cuboid = CastValue(dict[str, object], Camera["cuboid"])
    Cuboid["material"] = {
        "label": "Authored metal" if IsMetal else "Authored basic",
        "density_kg_m3": 7900.0 if IsMetal else 1150.0,
        "rgba": [0.25, 0.5, 0.75, 1.0],
    }
    Wrapper = {
        "schema": 1,
        "scope": "fixed_cuboid_authored_material_properties",
        "configuration_request": Config,
        "material_properties": KRichMetal if IsMetal else KRichBasic,
    }
    _ = Request.write_text(DumpJson(Wrapper), encoding="utf-8")
