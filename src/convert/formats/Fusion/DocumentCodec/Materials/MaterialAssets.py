from convert.formats.Fusion.DocumentCodec.Materials.BuildMatAsset import BuildMatAsset
from convert.formats.Fusion.DocumentCodec.Materials.Model.AssetFamily import AssetFamily
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialIds import MaterialIds
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode
from convert.formats.Fusion.MaterialCodec.Package.SchemaModels import SchemaModels


def MaterialAssets(
    SpecValue: MaterialSpec, Identity: MaterialIds, Nodes: tuple[SchemaNode, ...]
) -> tuple[MaterialAsset, ...]:
    Schemas = SchemaModels(Nodes)
    Indexed = {
        dict(Child.Attributes)["val"]: Schema
        for Schema in Nodes
        for Child in Schema.Children
        if Child.TagName == "UID"
    }
    Families = (
        AssetFamily(
            "PhysMatSchema",
            Identity.PhysicalId,
            Identity.PhysicalDef,
            "physicalmaterial",
            SpecValue.NameValue,
        ),
        AssetFamily(
            "StructuralMetalSchema",
            Identity.StructuralId,
            Identity.StructuralDef,
            "Structural",
            SpecValue.NameValue + " Structural",
        ),
        AssetFamily(
            "ThermalSolidSchema",
            Identity.ThermalId,
            Identity.ThermalDef,
            "Thermal",
            SpecValue.NameValue + " Thermal",
        ),
        AssetFamily(
            "PrismMetalSchema",
            Identity.AppearanceId,
            Identity.AppearanceDef,
            "materialappearance",
            SpecValue.NameValue + " Appearance",
        ),
    )
    return tuple(
        BuildMatAsset(SpecValue, Identity, Family, Indexed, Schemas)
        for Family in Families
    )
