# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace
from typing import cast

from CmgrOpening import ReadCmgrOpening
from CmgrVisualPrefix import CmgrVisualFields
from CmgrVisualProfile import KExplicitProfile
from ConfigRoot import OpenConfigRoot, ReadConfigRoot
from OrdinaryConfig import OrdinaryConfig
from OrdinaryPackage import KConfigManager, PackageState
from VisualState.VisualMaterialReadback import ReadVisualMaterial
from VisualState.VisualStateModel import CanonicalMaterial
from convert.adapters.solidworks.Container.Archive import KDefinitionKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Cmgr import KVisualClass
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KConfigStream


# caller color channels are independent of the archive integer byte order
def BindDocumentColor(
    Configuration: OrdinaryConfig, Package: PackageState, Channels: object
) -> tuple[OrdinaryConfig, PackageState]:
    RequireArch(
        isinstance(Channels, list)
        and len(Channels) == 3
        and all(type(Channel) is int and 0 <= Channel <= 255 for Channel in Channels),
        True,
        "explicit document RGB is a list of three integer bytes",
    )
    Red, Green, Blue = cast(list[int], Channels)
    Color = Red | (Green << 8) | (Blue << 16)
    Visual = replace(
        Package.Manager.Visual,
        SurfaceColor=Color,
        MaterialColor=Color,
        BumpStrength=KExplicitProfile.BumpStrength,
        DisplacementDistance=KExplicitProfile.DisplacementDistance,
        UsesNormalMap=KExplicitProfile.UsesNormalMap,
        UsesDefaultAppearance=KExplicitProfile.UsesDefaultAppearance,
    )
    return (
        replace(Configuration, First=replace(Configuration.First, Visual=Visual)),
        replace(Package, Manager=replace(Package.Manager, Visual=Visual)),
    )


# both inline owners must independently reread as the same generated appearance
def CheckInlineAppearances(
    Archive: SldprtArchive,
    Baseline: SldprtArchive,
    Generation: int,
    Expected: CmgrVisualFields,
) -> None:
    Manager = ReadCmgrOpening(Archive.require(KConfigManager), Generation)
    Inline, Split = OpenConfigRoot(Archive.require(KConfigStream))
    ReadConfigRoot(Inline, Generation)
    Inline.TakePointer((KVisualClass,), KDefinitionKind, CompactOnly=True)
    Fields = CanonicalMaterial(Expected)
    for Name, Cursor in ((KConfigManager, Manager), (KConfigStream, Inline)):
        Start = Cursor.Offset
        RequireArch(ReadVisualMaterial(Cursor, Generation), Fields, Name + " color")
        Old, New = Baseline.require(Name), Archive.require(Name)
        RequireArch(
            (New[:Start], New[Cursor.Offset:]),
            (Old[:Start], Old[Cursor.Offset:]),
            Name + " fields outside the generated appearance",
        )
    RequireArch(Inline.Offset <= Split, True, "appearance stays within first split")
