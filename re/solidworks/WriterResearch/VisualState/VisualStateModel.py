# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass, replace

from CmgrVisualPrefix import CmgrVisualFields, RequireVisualFields
from ColorAppearance import Float32
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

KVisualStateMember = "ThirdPtyStore/VisualStates"
KVisualRootClass = "visStateKeyData_c"
KHolderClass = "moCompHolder_c"
KFeatureClass = "moCompFeature_c"
KUnitClass = "moUnitComponent_c"
KMaterialClass = "visStateVisualPropertiesAttribute_c"
KAppearanceClass = "moVisualProperties_c"
KDisplayClass = "visStateVisualStateAttribute_c"


@dataclass(frozen=True, slots=True)
class VisualDisplay:
    Visible: bool
    DisplayMode: int
    EdgesInShadedMode: int
    HlrDisplayQuality: int


@dataclass(frozen=True, slots=True)
class VisualOwner:
    FeatureId: int | None
    Created: int | None
    Material: CmgrVisualFields | None
    Display: VisualDisplay


@dataclass(frozen=True, slots=True)
class VisualState:
    ConfigurationId: int
    RepresentationId: int
    Name: str
    Owners: tuple[VisualOwner, ...]


def CanonicalMaterial(Fields):
    if Fields is None:
        return None
    return replace(
        Fields,
        BumpStrength=Float32(Fields.BumpStrength),
        DisplacementDistance=Float32(Fields.DisplacementDistance),
    )


def CanonicalState(State):
    return replace(
        State,
        Owners=tuple(
            replace(Owner, Material=CanonicalMaterial(Owner.Material))
            for Owner in State.Owners
        ),
    )


def CheckVisualState(Generation: int, State: VisualState) -> None:
    RequireArch(
        type(Generation) is int and Generation == 19000, True, "visual-state generation"
    )
    RequireArch(isinstance(State, VisualState), True, "typed visual-state model")
    RequireArch(
        type(State.ConfigurationId) is int
        and 0 <= State.ConfigurationId <= 0x7FFFFFFF
        and type(State.RepresentationId) is int
        and 0 < State.RepresentationId <= 0x7FFFFFFF,
        True,
        "authored configuration and representation identities",
    )
    RequireArch(
        isinstance(State.Name, str)
        and bool(State.Name)
        and "\0" not in State.Name
        and len(State.Name.encode("utf-16-le")) // 2 < 65534,
        True,
        "bounded authored display-state name",
    )
    RequireArch(
        type(State.Owners) is tuple
        and 1 <= len(State.Owners) <= 64
        and all(isinstance(Owner, VisualOwner) for Owner in State.Owners)
        and State.Owners[0].FeatureId is None
        and State.Owners[0].Created is None
        and State.Owners[0].Material is not None,
        True,
        "standalone holder followed by authored feature owners",
    )
    RequireArch(
        sum(Owner.FeatureId is None for Owner in State.Owners),
        1,
        "one standalone visual holder",
    )
    Identities = []
    for Owner in State.Owners:
        Display = Owner.Display
        RequireArch(
            isinstance(Display, VisualDisplay)
            and type(Display.Visible) is bool
            and (
                Display.DisplayMode,
                Display.EdgesInShadedMode,
                Display.HlrDisplayQuality,
            )
            == (6, 1, 0)
            and all(
                type(Value) is int
                for Value in (
                    Display.DisplayMode,
                    Display.EdgesInShadedMode,
                    Display.HlrDisplayQuality,
                )
            ),
            True,
            "ordinary authored visibility and documented display settings",
        )
        if Owner.FeatureId is None:
            RequireArch(
                Owner is State.Owners[0], True, "unique standalone visual holder"
            )
            RequireArch(
                isinstance(Owner.Material, CmgrVisualFields),
                True,
                "typed holder appearance",
            )
            RequireVisualFields(Generation, Owner.Material, AllowSystemTexture=True)
        else:
            RequireArch(
                type(Owner.FeatureId) is int
                and 0 < Owner.FeatureId <= 0x7FFFFFFF
                and type(Owner.Created) is int
                and 0 <= Owner.Created <= 0xFFFFFFFF
                and Owner.Material is None,
                True,
                "feature creation identity with inherited appearance",
            )
            Identities.append(Owner.FeatureId)
    RequireArch(
        len(set(Identities)), len(Identities), "unique feature component owners"
    )
