from convert.Formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.Formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue


# independent native projection confirms altered material quantities instead of checking only the receipt
def CheckRichTrial(Material: MaterialSpec, IsMetal: bool) -> None:
    assert Material.Color == ColorValue(0.25, 0.5, 0.75, 1.0)
    if IsMetal:
        assert Material.NameValue == "Authored metal" and Material.Density == 7900.0
        assert Material.ClassName == "Metal" and Material.Finish.Metallic
        assert Material.Mechanics.YoungModulus == 182e9
        assert Material.Mechanics.Conductivity == 48.0
        assert Material.Thermal is not None and Material.Thermal.Emissivity == 0.65
        assert Material.Finish.Roughness == 0.35
        assert len(Material.Mechanics.Directional) == 5
    else:
        assert Material.NameValue == "Authored basic" and Material.Density == 1150.0
        assert Material.ClassName == "Basic" and Material.Thermal is None
        assert Material.Mechanics.Conductivity == 2.5
        assert Material.Mechanics.SpecificHeat == 780.0
        assert Material.Finish.Roughness == 0.4 and Material.Finish.Reflectance == 0.08
