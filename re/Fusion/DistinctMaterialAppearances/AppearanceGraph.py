# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import struct
from dataclasses import replace
from uuid import UUID

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields, SeriesItems
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.Materials.Model.MaterialIds import MaterialIds
from convert.Formats.Fusion.DocumentCodec.Materials.ProjectMaterial import ProjectMaterial

from AppearanceRequest import Material, SCHEMA, SCOPE, finish_record, require, validate
from AppearanceAssets import assemble
from MaterialGraph import COMPONENT_EMPTY, PACKAGE_PREFIX, PHYSICAL, ROLE_SCHEMAS

VISUAL = {
    *PHYSICAL,
    "CustomizedColor",
    "UseCustomizedColor",
    "proteinMaterialRotation",
    "proteinMaterialScale",
}


def owned_assets(package, physical_id, body_id):
    indexed = {asset.InstanceId: asset for asset in package.Assets}
    require(len(indexed) == len(package.Assets), "Repeated material asset identity")
    physical, body = indexed.get(physical_id), indexed.get(body_id)
    require(
        physical is not None
        and physical.AssetRole == "physicalmaterial"
        and physical.SchemaName == "PhysMatSchema",
        "Material lacks a direct physical owner",
    )
    require(
        body is not None
        and body.AssetRole == "materialappearance"
        and body.SchemaName in ROLE_SCHEMAS["materialappearance"],
        "Body lacks a direct modern appearance owner",
    )
    relations = [prop for prop in physical.Properties if prop.FieldName == "physmat_aspects"]
    require(len(relations) == 1, "Physical material does not have one aspect relation")
    links = relations[0].Connections
    require(links is not None and links.Enabled, "Physical material aspects are disabled")
    require(body_id not in links.Targets, "Body and physical aspect appearance must be distinct assets")
    roles = {}
    for target in links.Targets:
        asset = indexed.get(target)
        require(
            asset is not None
            and asset.AssetRole in {"Structural", "Thermal", "materialappearance"}
            and asset.AssetRole not in roles
            and asset.SchemaName in ROLE_SCHEMAS[asset.AssetRole],
            "Unsupported physical material aspect or role",
        )
        roles[asset.AssetRole] = asset
    require(
        {"Structural", "materialappearance"} <= roles.keys(),
        "Physical material misses an appearance or structure",
    )
    require(
        set(indexed) == {physical_id, body_id, *links.Targets},
        "Material package contains an extra or unowned asset",
    )
    roles["physicalmaterial"] = physical
    return roles, body, relations[0]


def check_binding(graph, manager, fields, asset, library):
    require(
        fields["assetReference"] == asset.InstanceId
        and fields["name"] == ""
        and fields["proteinMaterialID"] == asset.DefinitionId
        and fields["libraryID"] == library
        and graph.Resolve(fields["ProteinAssetManager"]) == manager,
        "Body bindings disagree with their direct owned material assets",
    )


def check_owner(graph, context, part, physical, visual, physical_asset, body_asset, body_color):
    manager = graph.OneClass("ProteinAssetManager")
    library = physical["libraryID"]
    require(type(library) is str and library, "Body material library identity is absent")
    check_binding(graph, manager, physical, physical_asset, library)
    check_binding(graph, manager, visual, body_asset, library)
    require(
        visual["UseCustomizedColor"] is False
        and visual["proteinMaterialRotation"] == 0.0
        and visual["proteinMaterialScale"] == 1.0,
        "Saved body material overrides or procedural mapping are unsupported",
    )
    expected_color = {
        name: struct.unpack("<f", struct.pack("<f", value))[0]
        for name, value in zip(("red", "green", "blue", "alpha"), Material.channels(body_color), strict=True)
    }
    require(
        ObjectFields(visual["CustomizedColor"]) == expected_color,
        "Body color cache disagrees with visible appearance",
    )
    default = ObjectFields(context.Component.Fields["defaultPhysicalMaterial"])
    linked = default == physical
    require(linked or default == COMPONENT_EMPTY, "Component default selects a different physical material")
    expected_refs = {
        "PhysicalMaterialAssetReferences": (physical_asset.InstanceId,),
        "PhysicalMaterialRefCountVector": (2 if linked else 1,),
        "VisualMaterialAssetReferences": (body_asset.InstanceId,),
        "VisualMaterialRefCountVector": (1,),
    }
    require(
        set(manager.Fields) == {*expected_refs, "partName"}
        and part.Name == PACKAGE_PREFIX + manager.Fields["partName"]
        and all(SeriesItems(manager.Fields[key]) == values for key, values in expected_refs.items()),
        "Material manager ownership vectors disagree with the distinct appearance routes",
    )
    return library, linked


def compare_package(part, roles, body, physical, body_color, body_finish, library):
    package = part.Package
    primary = roles["physicalmaterial"]
    structural = roles["Structural"]
    thermal = roles.get("Thermal")
    aspect = roles["materialappearance"]
    member = part.Name.removeprefix(PACKAGE_PREFIX)
    require(
        member.startswith("ProteinAsset.") and member.endswith(".protein"), "Unsupported material member name"
    )
    keys = [
        package.RootCore.Identifier,
        package.AssetCore.Identifier,
        library,
        member.removeprefix("ProteinAsset.").removesuffix(".protein"),
        *(asset.InstanceId for asset in package.Assets),
        *(asset.DefinitionId for asset in package.Assets),
    ]
    try:
        canonical = all(str(UUID(key)) == key for key in keys)
    except ValueError:
        canonical = False
    require(
        canonical and len(keys) == len(set(keys)),
        "Distinct material identities must be canonical and disjoint",
    )
    identities = MaterialIds(
        package.RootCore.Identifier,
        package.AssetCore.Identifier,
        library,
        primary.InstanceId,
        structural.InstanceId,
        "" if thermal is None else thermal.InstanceId,
        aspect.InstanceId,
        primary.DefinitionId,
        structural.DefinitionId,
        "" if thermal is None else thermal.DefinitionId,
        aspect.DefinitionId,
        member,
    )
    # Native IDs are bound only to compare this model with a fully reconstructed package.
    expected = assemble(
        physical,
        identities,
        body_color,
        body_finish,
        body.InstanceId,
        body.DefinitionId,
        package.RootCore.Created,
    )
    require(
        package == expected,
        "Distinct appearance package has unsupported fields, schemas, values or resources",
    )


def project_appearances(model):
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
    graph = BuildGraph(model)
    context = SelectExtrusion(graph)
    physical_binding = ObjectFields(context.BodyNode.Fields["physicalMaterial"])
    visual_binding = ObjectFields(context.BodyNode.Fields["visualMaterial"])
    require(
        set(physical_binding) == set(PHYSICAL) and set(visual_binding) == VISUAL,
        "Unsupported body material fields",
    )
    roles, body, relation = owned_assets(
        package, physical_binding["assetReference"], visual_binding["assetReference"]
    )
    primary = roles["physicalmaterial"]
    aspect = roles["materialappearance"]
    physical = ProjectMaterial(package, primary.InstanceId)

    # Reuse the SDK finish projection on a temporary read-only view of the independently resolved body asset.
    links = replace(
        relation.Connections,
        Targets=tuple(
            body.InstanceId if target == aspect.InstanceId else target
            for target in relation.Connections.Targets
        ),
    )
    view = replace(
        primary,
        Properties=tuple(
            replace(prop, Connections=links) if prop == relation else prop for prop in primary.Properties
        ),
    )
    body_spec = ProjectMaterial(
        replace(package, Assets=tuple(view if asset == primary else asset for asset in package.Assets)),
        primary.InstanceId,
    )
    library, linked = check_owner(
        graph, context, part, physical_binding, visual_binding, primary, body, body_spec.Color
    )
    compare_package(part, roles, body, physical, body_spec.Color, body_spec.Finish, library)
    return physical, linked, body_spec.Color, body_spec.Finish, aspect, body


def projection(model, public):
    physical, component_default, body_color, body_finish, _, _ = project_appearances(model)
    request = {
        "schema": SCHEMA,
        "scope": SCOPE,
        "material_request": {
            "schema": Material.SCHEMA,
            "scope": Material.SCOPE,
            "configuration_request": Material.Config.projection(model, public),
            "material_properties": Material.material_properties(physical, component_default),
        },
        "physical_appearance_rgba": Material.channels(physical.Color),
        "body_finish": finish_record(body_finish),
    }
    _, checked, linked, color, finish = validate(request)
    require(
        (checked, linked, color, finish) == (physical, component_default, body_color, body_finish),
        "Distinct appearances lie outside the explicit material request roles",
    )
    return request


def prepare(source):
    return projection(*Material.Config.Cameras.open_saved(source))
