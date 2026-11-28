# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace
from uuid import UUID, uuid5

from convert.Formats.Fusion.DocumentCodec.Materials.BuildMatAsset import BuildMatAsset
from convert.Formats.Fusion.DocumentCodec.Materials.BuildMaterial import SchemaClosure
from convert.Formats.Fusion.DocumentCodec.Materials.MaterialAssets import (
    IndexSchemas,
    MakeFamily,
    MaterialAssets,
)
from convert.Formats.Fusion.DocumentCodec.Materials.MatProperties import FinishProps
from convert.Formats.Fusion.DocumentCodec.Materials.PlanMaterial import FinishSchema
from convert.Formats.Fusion.DocumentCodec.Materials.SchemaFields import SchemaFields
from convert.Formats.Fusion.DocumentCodec.Materials.VisualValue import VisualValue
from convert.Formats.Fusion.DocumentCodec.Materials.Vocabulary.ReadMatSchema import ReadMatSchema
from convert.Formats.Fusion.MaterialCodec.Models.PropertyValue import PropertyValue
from convert.Formats.Fusion.MaterialCodec.Package.MakePackage import MakePackage
from convert.Formats.Fusion.MaterialCodec.Package.SchemaModels import SchemaModels

from AppearanceRequest import Material, require


def build_body_asset(physical, body_color, body_finish, instance, definition, library, schemas):
    indexed = IndexSchemas(schemas)
    schema, local = FinishSchema(body_finish, indexed)
    require(local in ("Metal", "Opaque"), "Unsupported body finish encoding")
    semantic = replace(physical, Color=body_color, Finish=body_finish)
    properties = FinishProps(semantic, SchemaFields(schema, indexed), local)
    family = MakeFamily(
        schema,
        instance,
        definition,
        body_finish.NameValue,
        (PropertyValue("AssetLibID", library), *properties),
        indexed,
    )
    return BuildMatAsset(family, indexed, SchemaModels(schemas))


def assemble(physical, identities, body_color, body_finish, instance, definition, stamp):
    schemas = ReadMatSchema()
    primary = MaterialAssets(physical, identities, schemas)
    extra = build_body_asset(
        physical, body_color, body_finish, instance, definition, identities.LibraryId, schemas
    )
    assets = (*primary, extra)
    return MakePackage(
        identities.PackageId,
        identities.AssetId,
        stamp,
        SchemaClosure(tuple(asset.SchemaName for asset in assets), schemas),
        assets,
    )


def stage_body_appearance(author, body_color, body_finish):
    material = author.Materials
    require(material is not None, "Fresh constructor lacks a material package")
    identity = material.Identity
    namespace = UUID(identity.PackageId)
    instance = str(uuid5(namespace, "kit:fusion:direct-body-appearance:instance"))
    definition = str(uuid5(namespace, "kit:fusion:direct-body-appearance:definition"))
    package = assemble(
        author.SpecValue.Material,
        identity,
        body_color,
        body_finish,
        instance,
        definition,
        material.Package.RootCore.Created,
    )
    require(
        package.Assets[:-1] == material.Package.Assets,
        "Distinct appearance changed the fresh physical package",
    )
    author.Materials = replace(material, Package=package)
    visual = VisualValue(author)
    visual[0]["fields"].update(
        assetReference=instance,
        proteinMaterialID=definition,
        CustomizedColor=dict(
            zip(("red", "green", "blue", "alpha"), Material.channels(body_color), strict=True)
        ),
    )
    author.Change("body", visualMaterial=visual)
    author.Change("protein", VisualMaterialAssetReferences=[instance])
    return author
