from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Core.TypedResolved.Materials.NamedMatRead import (
    NamedMatRead,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument

# the body attribute names the verified native physical assignment and owner evidence
KPartMaterial = "solidworks.assigned_part_material"


# physical material data belongs to the selected body and configuration it can actually identify
def AttachMatRead(
    DocumentValue: CadDocument, MaterialValue: NamedMatRead
) -> CadDocument:
    if len(DocumentValue.bodies) != 1 or len(DocumentValue.configurations) != 1:
        raise BodyUnsupported(
            "SOLIDWORKS material has no sole SDK body and configuration"
        )
    (BodyValue,) = DocumentValue.bodies
    (ConfigValue,) = DocumentValue.configurations
    if (
        not ConfigValue.active
        or ConfigValue.name != MaterialValue.CfgName
        or BodyValue.material_id is not None
        or BodyValue.topology.solid_count != 1
        or not any(
            StepValue.id == BodyValue.final_feature_id
            and StepValue.attributes.get("native_object_id") == MaterialValue.FeatureId
            for StepValue in DocumentValue.feature_timeline
        )
    ):
        raise BodyUnsupported(
            "SOLIDWORKS material disagrees with the projected SDK body owner"
        )
    Assignment = FreezeMapping(
        {
            "configuration_id": ConfigValue.id,
            "configuration_name": ConfigValue.name,
            "catalog": MaterialValue.CatalogValue,
            "name": MaterialValue.MaterialName,
            "native_material_id": MaterialValue.NativeId,
            "density_kg_m3": MaterialValue.DensityValue,
            "native_atom_id": MaterialValue.AtomId,
            "native_feature_id": MaterialValue.FeatureId,
        }
    )
    BodyValue = ReplaceValue(
        BodyValue,
        attributes=FreezeMapping(
            dict(BodyValue.attributes) | {KPartMaterial: Assignment}
        ),
    )
    return ReplaceValue(DocumentValue, bodies=(BodyValue,))
