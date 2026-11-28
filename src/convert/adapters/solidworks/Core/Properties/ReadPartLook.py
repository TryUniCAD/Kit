from collections.abc import Mapping
from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Config.Material.ReadPartVisual import (
    ReadPartVisual,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive


# independent native color domains must keep their stored channel order for comparison
def ColorRef(Value: object) -> tuple[int, int, int]:
    if type(Value) is not int or not 0 <= Value <= 0xFFFFFF:
        raise ValueError("stored SOLIDWORKS COLORREF has unsupported high bits")
    return Value & 255, (Value >> 8) & 255, (Value >> 16) & 255


# the stored color and optical fields may not publish nonfinite json values
def OpticalValue(Value: object) -> float:
    if type(Value) not in (float, int):
        raise ValueError("stored SOLIDWORKS optical field is not numeric")
    Result = float(CastValue(float, Value))
    if not IsFinite(Result):
        raise ValueError("stored SOLIDWORKS optical field is not finite")
    return Result


# native texture fields lack confirmed mapping semantics but need their exact wire keys
def WireTexture(Material: Mapping[str, object]) -> dict[str, object] | None:
    if Material["has80"] == 0:
        return None
    Values = CastValue(Mapping[str, object], Material["f80"])
    if any(type(Value) is float and not IsFinite(Value) for Value in Values.values()):
        raise ValueError("stored SOLIDWORKS texture contains a nonfinite field")
    return dict(Values)


# stored appearance keeps document color independent from physical assignment and effective body color
def ReadPartLook(Archive: SldprtArchive) -> dict[str, object]:
    Graph = ReadPartVisual(Archive)
    Visual = Graph.VisualValue.FieldsValue
    Material = CastValue(Mapping[str, object], Visual["f20"])
    Classic = CastValue(Mapping[str, object], Material["f90"])
    PbrValues = CastValue(Mapping[str, object], Visual["f88"])
    BasicPbr = (
        {
            "albedo": tuple(
                OpticalValue(PbrValues[f"f10_{Index}"]) for Index in range(3)
            ),
            "metallic": OpticalValue(PbrValues["f28"]),
            "roughness": OpticalValue(PbrValues["f2c"]),
        }
        if (PbrValues["f00"], PbrValues["f08"]) == ("2025x", "basic")
        else None
    )
    return {
        "scope": "stored_part_visual",
        "stream": "Contents/Config-0",
        "record": "moVisualProperties_c",
        "record_end": Graph.NextOffset,
        "stored_label": Material["f20"],
        "model_rgb": ColorRef(Visual["f0c"]),
        "hidden_line_rgb": ColorRef(Visual["f18"]),
        "legacy_optics": {
            "ambient": OpticalValue(Material["f38"]),
            "diffuse": OpticalValue(Material["f40"]),
            "specular": OpticalValue(Material["f48"]),
            "shininess": OpticalValue(Material["f50"]),
            "transparency": OpticalValue(Material["f58"]),
        },
        "classic_renderer": {
            "primary_rgb": ColorRef(Classic["f14"]),
            "resource_locator": Classic["f68"],
            "roughness": OpticalValue(Classic["f74"]),
        },
        "basic_pbr": BasicPbr,
        "primary_texture_wire": WireTexture(Material),
        "effective_body_appearance": None,
    }
