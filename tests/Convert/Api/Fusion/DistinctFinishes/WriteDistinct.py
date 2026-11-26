from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Api.Fusion.SavedMaterials.RichMatInputs import KRichBasic


# distinct body color and physical aspect color expose a collapsed finish binding
def WriteDistinct(MaterialPath: FilePath, Request: FilePath, Roughness: float) -> None:
    Material = CastValue(
        dict[str, object], LoadJson(MaterialPath.read_text(encoding="utf-8"))
    )
    BodyFinish = CastValue(dict[str, object], KRichBasic["finish"])
    Wrapper = {
        "schema": 1,
        "scope": "fixed_cuboid_distinct_material_appearances",
        "material_request": Material,
        "physical_appearance_rgba": [0.75, 0.125, 0.375, 1.0],
        "body_finish": {
            **BodyFinish,
            "name": "Body-only matte finish",
            "roughness": Roughness,
        },
    }
    _ = Request.write_text(DumpJson(Wrapper), encoding="utf-8")
