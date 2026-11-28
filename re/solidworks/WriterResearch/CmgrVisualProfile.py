# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch


# measured ordinary color branches share their wire grammar without sharing material policy
@dataclass(frozen=True, slots=True)
class CmgrProfile:
    LegacyWords: tuple[int, ...]
    ReflectivityTerms: tuple[float | int, ...]
    SpecularTerms: tuple[float | int, ...]
    SurfaceFlags: int
    UsesNormalMap: bool
    BumpStrength: float
    DisplacementDistance: float
    UsesDefaultAppearance: bool
    SystemTexturePath: str


# existing discovery inverses require their original default material and surface conventions
KDefaultProfile = CmgrProfile(
    (1, 0, 1, 1, 1),
    (0.05, 0, -1, -1, -1, 0, 0, 0),
    (0xFFFFFF, 0.6, 1),
    0x140,
    True,
    0.001,
    0.001,
    True,
    r"<SystemTexture>\graphics\materials\color.p2m",
)


# native model color setters select a distinct measured untextured appearance policy
KExplicitProfile = CmgrProfile(
    (1, 0, 1, 0, 1),
    (0.1, 0, 1, 1, 0.5, 0, 0, 0),
    (0xFFFFFF, 0.0032, 1),
    0x44,
    False,
    0.00001,
    0.005,
    False,
    r"<SystemTexture>\graphics\Materials\color.p2m",
)


# explicit false selects the new branch while existing default callers retain their contract
def SelectVisualProfile(UsesDefaultAppearance) -> CmgrProfile:
    if UsesDefaultAppearance is False:
        return KExplicitProfile
    RequireArch(UsesDefaultAppearance, True, "ordinary default appearance selection")
    return KDefaultProfile
