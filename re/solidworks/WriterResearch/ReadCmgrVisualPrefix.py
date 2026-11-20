# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from struct import pack as PackFields

from CmgrVisualPrefix import CmgrVisualFields, KDefaultShader, RequireVisualFields
from CmgrVisualProfile import KDefaultProfile, KExplicitProfile, SelectVisualProfile
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor


# exact encoded scalar comparisons retain float widths while rejecting unsupported profile mixtures
def ReadVisualValues(Cursor, Format, Expected, Field):
    Actual = Cursor.ReadValue(Format)
    RequireArch(PackFields(Format, *Actual), PackFields(Format, *Expected), Field)
    return Actual


# a shared material walk keeps partial legacy readers and complete prefixes on one grammar
def ReadMaterialFields(Cursor: FieldCursor):
    RequireArch(
        (Cursor.ReadText(), Cursor.ReadText()),
        ("", "Steel"),
        "CMgr ordinary material names",
    )
    ReadVisualValues(
        Cursor,
        "<6di",
        (1, 1, 0.5, 0.3125, 0, 0, 0),
        "CMgr ordinary material coefficients",
    )
    Legacy = Cursor.ReadInts("<5i")
    RequireArch(
        Legacy in (KDefaultProfile.LegacyWords, KExplicitProfile.LegacyWords),
        True,
        "CMgr supported legacy material profile",
    )
    Profile = SelectVisualProfile(bool(Legacy[3]))
    RequireArch(
        (Cursor.ReadText(), Cursor.ReadInts("<2i")),
        ("", (1, 1)),
        "CMgr RealView appearance presence",
    )
    (AppearanceId,) = Cursor.ReadInts("<Q")
    RequireArch(Cursor.ReadText(), KDefaultShader, "CMgr RealView shader")
    MappingMode, MaterialColor = Cursor.ReadInts("<BI")
    ReadVisualValues(
        Cursor,
        "<10fi",
        (1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1),
        "CMgr ordinary mapping frame and color form",
    )
    ReadVisualValues(
        Cursor, "<5fi2f", Profile.ReflectivityTerms, "CMgr profile reflectivity terms"
    )
    Locator = Cursor.ReadText()
    ReadVisualValues(
        Cursor, "<I2f", Profile.SpecularTerms, "CMgr profile specular terms"
    )
    RequireArch(Cursor.ReadText(), "", "CMgr absent auxiliary texture")
    Bump, Displacement, _, _, _, _ = ReadVisualValues(
        Cursor,
        "<3fifi",
        (
            Profile.BumpStrength,
            Profile.DisplacementDistance,
            0,
            Profile.SurfaceFlags,
            0,
            0,
        ),
        "CMgr profile bump surface terms",
    )
    ReadVisualValues(
        Cursor,
        "<13f",
        (1, 0, 0, 0, 1, 0, 0, 0, 1, 90, 1, -1, -1),
        "CMgr ordinary secondary mapping frame",
    )
    RequireArch(Cursor.ReadText(), "", "CMgr empty auxiliary material string")
    ReadVisualValues(Cursor, "<f", (0,), "CMgr ordinary auxiliary material value")
    return {
        "MaterialName": "Steel",
        "AppearanceId": AppearanceId,
        "MaterialColor": MaterialColor,
        "NativeAssetPath": Locator,
        "MappingMode": MappingMode,
        "BumpStrength": Bump,
        "DisplacementDistance": Displacement,
        "UsesNormalMap": Profile.UsesNormalMap,
        "UsesDefaultAppearance": Profile.UsesDefaultAppearance,
    }


# full prefix ownership must agree across the legacy profile and outer default appearance word
def ReadCmgrVisualPrefix(
    Cursor: FieldCursor, Generation: int, *, AllowSystemTexture: bool = False
) -> CmgrVisualFields:
    Colors = Cursor.ReadInts("<3I")
    Material = ReadMaterialFields(Cursor)
    RequireArch(
        (Cursor.ReadText(), Cursor.ReadInts("<2i")),
        ("", (0, 0)),
        "CMgr empty material suffix",
    )
    RequireArch(
        (
            Cursor.ReadText(),
            Cursor.ReadInts("<2i"),
            Cursor.ReadText(),
            Cursor.ReadInts("<6i"),
        ),
        ("", (0, 1), "", (0, int(Material["UsesDefaultAppearance"]), -1, 0, 0, 1)),
        "CMgr consistent profile and DSPBR appearance presence",
    )
    Fields = CmgrVisualFields(*Colors, **Material)
    RequireVisualFields(Generation, Fields, AllowSystemTexture=AllowSystemTexture)
    return Fields
