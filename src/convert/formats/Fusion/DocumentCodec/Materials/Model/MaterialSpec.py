from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue


@MakeDataClass(frozen=True, slots=True)
class MaterialSpec:
    NameValue: str = "Kit Generic Material"
    Density: float = 1000.0
    Color: ColorValue = ColorValue(0.8, 0.8, 0.8, 1.0)
