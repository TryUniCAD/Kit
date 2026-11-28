# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace

from CmgrOpening import KFirstConfigurationId
from CmgrVisualProfile import KDefaultProfile
from ResolvedOrigin import KOriginTreeId
from VisualState.VisualStateArchive import EncodeVisualState
from VisualState.VisualStateModel import (
    CanonicalMaterial,
    CheckVisualState,
    KVisualStateMember,
    VisualDisplay,
    VisualOwner,
    VisualState,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch


def MakePackageVisuals(State, Profile, System, RepresentationId, Name, Visibility):
    Features = (
        Profile.Feature.TreeId,
        KOriginTreeId,
        *(Plane.TreeId for Plane in System.Planes),
    )
    RequireArch(
        type(Visibility) is dict
        and set(Visibility) == {"holder", *(str(Id) for Id in Features)},
        True,
        "explicit visibility for every visual owner",
    )
    RequireArch(
        all(type(Value) is bool for Value in Visibility.values()),
        True,
        "authored Boolean visibility",
    )
    Created = {Log.TreeId: Log.CreatedTime for Log in State.Header.Logs.Revisions}
    Material = State.Manager.Visual
    if Material.UsesDefaultAppearance:
        Material = replace(
            Material, NativeAssetPath=KDefaultProfile.SystemTexturePath
        )
    Owners = [
        VisualOwner(None, None, Material, VisualDisplay(Visibility["holder"], 6, 1, 0))
    ]
    for Id in Features:
        RequireArch(Id in Created, True, "visual owner has an authored feature log")
        Owners.append(
            VisualOwner(
                Id, Created[Id], None, VisualDisplay(Visibility[str(Id)], 6, 1, 0)
            )
        )
    return VisualState(KFirstConfigurationId, RepresentationId, Name, tuple(Owners))


def EncodePackageVisuals(
    Generation, State, Profile, System, Header, Manager, Definition
):
    if State is None:
        return {}
    CheckVisualState(Generation, State)
    RequireArch(
        State.ConfigurationId,
        KFirstConfigurationId,
        "same standalone package configuration",
    )
    Features = {
        Profile.Feature.TreeId,
        KOriginTreeId,
        *(Plane.TreeId for Plane in System.Planes),
    }
    Owners = {Owner.FeatureId: Owner for Owner in State.Owners[1:]}
    RequireArch(
        set(Owners), Features, "same generated profile and system visual owners"
    )
    Created = {Log.TreeId: Log.CreatedTime for Log in Header.Logs.Revisions}
    RequireArch(
        all(
            Identity in Created and Owner.Created == Created[Identity]
            for Identity, Owner in Owners.items()
        ),
        True,
        "visual references use their own feature creation logs",
    )
    Material = State.Owners[0].Material
    Comparable = Material
    if Material.UsesDefaultAppearance:
        Comparable = replace(Material, NativeAssetPath=Manager.Visual.NativeAssetPath)
    RequireArch(
        CanonicalMaterial(Comparable),
        CanonicalMaterial(Manager.Visual),
        "holder copies the authored configuration appearance",
    )
    RequireArch(
        Material.AppearanceId < Definition.AppearanceCounter < 1 << 64,
        True,
        "document appearance allocator follows its assigned identity",
    )
    return {KVisualStateMember: EncodeVisualState(Generation, State)}
