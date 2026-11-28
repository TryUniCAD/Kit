from math import isclose as IsClose

from convert.adapters.Fusion.Measurement.IsFuseGeom import IsFuseGeom
from convert.adapters.Fusion.Measurement.ReadFuseMeas import (
    ReadMeasList,
    ReadMeasMap,
    ReadMeasNum,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec


# the snapshot must retain the requested independent driver and its measured value
def CheckDriver(
    State: dict[str, object], SpecValue: DocumentSpec, HeightMm: float
) -> None:
    Parameters = tuple(
        ReadMeasMap(ItemValue) for ItemValue in ReadMeasList(State.get("parameters"))
    )
    Names = (
        (SpecValue.ParamName, HeightMm),
        (SpecValue.WidthParamName, SpecValue.WidthMm),
        (SpecValue.DepthParamName, SpecValue.DepthMm),
    )
    for NameText, Expected in Names:
        Matches = tuple(
            ItemValue for ItemValue in Parameters if ItemValue.get("name") == NameText
        )
        if (
            len(Matches) != 1
            or Matches[0].get("unit") != "cm"
            or not IsClose(
                ReadMeasNum(Matches[0].get("value")) * 10.0,
                Expected,
                rel_tol=1e-8,
                abs_tol=1e-7,
            )
        ):
            raise ValueError("Fusion measurement does not preserve the cuboid drivers")


# geometry derives from the model so receipt values cannot dictate expected measurements
def CheckFuseCube(
    State: dict[str, object], SpecValue: DocumentSpec, HeightMm: float
) -> None:
    Width, Depth = SpecValue.WidthMm, SpecValue.DepthMm
    Expected = [
        {
            "name": SpecValue.BodyName,
            "faces": 6,
            "edges": 12,
            "vertices": 8,
            "volume_mm3": Width * Depth * HeightMm,
            "center_mm": [Width / 2.0, Depth / 2.0, HeightMm / 2.0],
            "bounds_mm": [[0.0, 0.0, 0.0], [Width, Depth, HeightMm]],
        }
    ]
    if HeightMm <= 0.0 or not IsFuseGeom(State["bodies"], Expected):
        raise ValueError(
            "Fusion measurement disagrees with the expected cuboid geometry"
        )
