# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import struct
from uuid import UUID

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields, SeriesItems
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.Materials.BuildMaterial import SchemaClosure
from convert.Formats.Fusion.DocumentCodec.Materials.MaterialAssets import MaterialAssets
from convert.Formats.Fusion.DocumentCodec.Materials.Model.MaterialIds import MaterialIds
from convert.Formats.Fusion.DocumentCodec.Materials.ProjectMaterial import ProjectMaterial
from convert.Formats.Fusion.DocumentCodec.Materials.Vocabulary.ReadMatSchema import ReadMatSchema
from convert.Formats.Fusion.MaterialCodec.Package.MakePackage import MakePackage

from MaterialRequest import Config, SCHEMA, SCOPE, channels, material_properties, require, validate

PACKAGE_PREFIX = "ProteinAssets.BlobParts/"
PHYSICAL = ("ProteinAssetManager", "assetReference", "libraryID", "name", "proteinMaterialID")
COMPONENT_EMPTY = {key: None if key == "ProteinAssetManager" else "" for key in PHYSICAL}
ROLE_SCHEMAS = {
    "physicalmaterial": {"PhysMatSchema"},
    "materialappearance": {"PrismMetalSchema", "PrismOpaqueSchema"},
    "Structural": {"StructuralMetalSchema", "StructuralBasicSchema"},
    "Thermal": {"ThermalSolidSchema"},
}


def canonical_package(part, spec, roles, library):
    package = part.Package
    physical = roles["physicalmaterial"]
    structural = roles["Structural"]
    finish = roles["materialappearance"]
    thermal = roles.get("Thermal")
    identities = MaterialIds(
        package.RootCore.Identifier,
        package.AssetCore.Identifier,
        library,
        physical.InstanceId,
        structural.InstanceId,
        "" if thermal is None else thermal.InstanceId,
        finish.InstanceId,
        physical.DefinitionId,
        structural.DefinitionId,
        "" if thermal is None else thermal.DefinitionId,
        finish.DefinitionId,
        part.Name.removeprefix(PACKAGE_PREFIX),
    )
    if not identities.PartName.startswith("ProteinAsset.") or not identities.PartName.endswith(".protein"):
        raise ValueError("Material package has an unsupported part name")
    part_identity = identities.PartName.removeprefix("ProteinAsset.").removesuffix(".protein")
    keys = [
        identities.PackageId,
        identities.AssetId,
        identities.LibraryId,
        part_identity,
        *(asset.InstanceId for asset in package.Assets),
        *(asset.DefinitionId for asset in package.Assets),
    ]
    try:
        canonical = all(str(UUID(key)) == key for key in keys)
    except ValueError:
        canonical = False
    require(canonical and len(keys) == len(set(keys)), "Material identities must be canonical and disjoint")

    # Bind identities only for comparing the read package. The request keeps no IDs.
    schemas = ReadMatSchema()
    assets = MaterialAssets(spec, identities, schemas)
    expected = MakePackage(
        identities.PackageId,
        identities.AssetId,
        package.RootCore.Created,
        SchemaClosure(tuple(asset.SchemaName for asset in assets), schemas),
        assets,
    )
    require(package == expected, "Material package has unsupported fields, schemas, values or resources")


def project_material(model):
    require(len(model.Materials) == 1, "Expected one body material package")
    (part,) = model.Materials
    package = part.Package
    require(package.Resources is None, "Saved material package resources are unsupported")
    require(
        all(
            asset.SchemaName != "GenericSchema" and not asset.InstanceId.endswith("_Post2015")
            for asset in package.Assets
        ),
        "Saved material compatibility aliases are unsupported (GenericSchema / _Post2015)",
    )
    require(model.Graphics is None, "Saved graphics and procedural material mapping are unsupported here")

    roles = {}
    for asset in package.Assets:
        require(
            asset.AssetRole not in roles and asset.SchemaName in ROLE_SCHEMAS.get(asset.AssetRole, ()),
            "Saved material has an unsupported or unowned aspect schema",
        )
        roles[asset.AssetRole] = asset
    require(
        {"physicalmaterial", "materialappearance", "Structural"} <= roles.keys(),
        "Material requires a body physical asset and single structural and visual aspects",
    )
    graph = BuildGraph(model)
    context = SelectExtrusion(graph)
    manager = graph.OneClass("ProteinAssetManager")
    physical = ObjectFields(context.BodyNode.Fields["physicalMaterial"])
    visual = ObjectFields(context.BodyNode.Fields["visualMaterial"])
    physical_asset, visual_asset = roles["physicalmaterial"], roles["materialappearance"]
    library = physical.get("libraryID")
    require(type(library) is str and library, "Body physical material library identity is absent")
    for binding, asset in ((physical, physical_asset), (visual, visual_asset)):
        expected = {
            "assetReference": asset.InstanceId,
            "libraryID": library,
            "name": "",
            "proteinMaterialID": asset.DefinitionId,
        }
        require(
            all(binding.get(key) == value for key, value in expected.items())
            and graph.Resolve(binding["ProteinAssetManager"]) == manager,
            "Body material references do not select the canonical physical and appearance aspects",
        )
    require(set(physical) == set(PHYSICAL), "Unsupported body physical material fields")
    require(
        set(visual)
        == {
            *PHYSICAL,
            "CustomizedColor",
            "UseCustomizedColor",
            "proteinMaterialRotation",
            "proteinMaterialScale",
        }
        and visual["UseCustomizedColor"] is False
        and visual["proteinMaterialRotation"] == 0.0
        and visual["proteinMaterialScale"] == 1.0,
        "Saved body material overrides or procedural mapping are unsupported",
    )
    default = ObjectFields(context.Component.Fields["defaultPhysicalMaterial"])
    component_default = default == physical
    require(
        component_default or default == COMPONENT_EMPTY,
        "Component default selects a different physical material",
    )
    expected_refs = {
        "PhysicalMaterialAssetReferences": (physical_asset.InstanceId,),
        "PhysicalMaterialRefCountVector": (2 if component_default else 1,),
        "VisualMaterialAssetReferences": (visual_asset.InstanceId,),
        "VisualMaterialRefCountVector": (1,),
    }
    require(
        set(manager.Fields) == {*expected_refs, "partName"}
        and part.Name == PACKAGE_PREFIX + manager.Fields["partName"]
        and all(SeriesItems(manager.Fields[key]) == value for key, value in expected_refs.items()),
        "Material manager ownership vectors disagree with the body or component",
    )
    spec = ProjectMaterial(package, physical_asset.InstanceId)
    expected_color = {
        name: struct.unpack("<f", struct.pack("<f", value))[0]
        for name, value in zip(("red", "green", "blue", "alpha"), channels(spec.Color), strict=True)
    }
    require(
        ObjectFields(visual["CustomizedColor"]) == expected_color,
        "Body color cache disagrees with appearance",
    )
    canonical_package(part, spec, roles, library)
    return spec, component_default


def projection(model, public):
    spec, component_default = project_material(model)
    request = {
        "schema": SCHEMA,
        "scope": SCOPE,
        "configuration_request": Config.projection(model, public),
        "material_properties": material_properties(spec, component_default),
    }
    _, checked, _ = validate(request)
    require(checked == spec, "Material properties lie outside the explicit Basic and Metal request roles")
    return request


def prepare(source):
    return projection(*Config.Cameras.open_saved(source))
