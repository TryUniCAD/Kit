from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialIds import MaterialIds
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.formats.Fusion.MaterialCodec.Models.AssetLinks import AssetLinks
from convert.formats.Fusion.MaterialCodec.Models.PropertyValue import PropertyValue
from convert.formats.Fusion.MaterialCodec.Models.UnitValue import UnitValue


def MatProperties(
    SpecValue: MaterialSpec, Identity: MaterialIds, SchemaName: str
) -> tuple[PropertyValue, ...]:
    Common = (PropertyValue("AssetLibID", Identity.LibraryId),)
    if SchemaName == "PhysMatSchema":
        return Common + (
            PropertyValue("physmat_Label", SpecValue.NameValue),
            PropertyValue(
                "physmat_aspects",
                None,
                AssetLinks(
                    True,
                    (Identity.StructuralId, Identity.ThermalId, Identity.AppearanceId),
                ),
            ),
        )
    if SchemaName == "PrismMetalSchema":
        return Common + (PropertyValue("metal_f0", SpecValue.Color),)
    if SchemaName == "StructuralMetalSchema":
        return Common + (
            PropertyValue("structural_Density", UnitValue(69633, SpecValue.Density)),
        )
    if SchemaName == "ThermalSolidSchema":
        return Common + (
            PropertyValue("thermal_Density", UnitValue(69633, SpecValue.Density)),
        )
    raise ValueError("Unsupported authored material family")
