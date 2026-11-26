# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from VisualState.VisualMaterialReadback import ReadVisualMaterial
from VisualState.VisualStateModel import (
    CheckVisualState,
    KAppearanceClass,
    KDisplayClass,
    KFeatureClass,
    KHolderClass,
    KMaterialClass,
    KUnitClass,
    KVisualRootClass,
    VisualDisplay,
    VisualOwner,
    VisualState,
)
from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KObjectRefKind,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor


def ReadNewObject(Cursor, Names):
    Tag, Name, Index = Cursor.TakePointer(Names, CompactOnly=True)
    RequireArch(
        Tag.kind in (KDefinitionKind, KClassRefKind), True, "new visual-state object"
    )
    return Name, Index


def ReadComponent(Cursor, Generation):
    Name, _ = ReadNewObject(Cursor, (KHolderClass, KFeatureClass))
    ReadNewObject(Cursor, (KUnitClass,))
    Cursor.ReadNull()
    RequireArch(
        Cursor.ReadInts("<B"), (0,), "standalone component has no external object"
    )
    RequireArch(
        Cursor.ReadInts("<6i"), (0,) * 6, "ordinary self-component reference state"
    )
    RequireArch(
        Cursor.ReadInts("<iiIi"),
        (0, 0, 0, 0),
        "absent component record and native selectors",
    )
    RequireArch(
        Cursor.ReadInts("<4i"), (-1,) * 4, "unset component-reference selectors"
    )
    RequireArch(Cursor.ReadInts("<5i"), (0,) * 5, "absent component-reference children")
    RequireArch(Cursor.ReadInts("<I"), (Generation,), "component-reference generation")
    if Name == KHolderClass:
        return None, None
    return Cursor.ReadInts("<iI")


def ReadMaterial(Cursor, Generation, Cache):
    Tag, _, Index = Cursor.TakePointer((KMaterialClass,), CompactOnly=True)
    if Tag.kind == KObjectRefKind:
        RequireArch(Index in Cache, True, "previously decoded visual attribute")
        return Cache[Index]
    RequireArch(Cursor.ReadInts("<I"), (1,), "visual attribute base selector")
    Tag, Name, _ = Cursor.TakePointer((KAppearanceClass, None), CompactOnly=True)
    if Name is None:
        Value = None
    else:
        RequireArch(
            Tag.kind in (KDefinitionKind, KClassRefKind),
            True,
            "owned appearance object",
        )
        Value = ReadVisualMaterial(Cursor, Generation, AllowSystemTexture=True)
    RequireArch(Value not in Cache.values(), True, "interned ordinary visual attribute")
    Cache[Index] = Value
    return Value


def ReadDisplay(Cursor, Cache):
    Tag, _, Index = Cursor.TakePointer((KDisplayClass,), CompactOnly=True)
    if Tag.kind == KObjectRefKind:
        RequireArch(Index in Cache, True, "previously decoded display attribute")
        return Cache[Index]
    Selector, Visibility, Mode, Edges, Quality = Cursor.ReadInts("<I4i")
    RequireArch(
        (Selector, Visibility in (0, 1)), (1, True), "Boolean visual-state visibility"
    )
    Value = VisualDisplay(bool(Visibility), Mode, Edges, Quality)
    RequireArch(
        Value not in Cache.values(), True, "interned ordinary display attribute"
    )
    Cache[Index] = Value
    return Value


def DecodeVisualState(Data, Generation):
    RequireArch(
        isinstance(Data, bytes) and len(Data) <= 2 * 1024 * 1024,
        True,
        "bounded visual-state stream",
    )
    Cursor = ArchiveCursor(Data, 0, 1, {}, {})
    RequireArch(
        Cursor.ReadInts("<Ii"), (Generation, 0), "standalone visual-state header"
    )
    Cursor.TakePointer((KVisualRootClass,), KDefinitionKind, CompactOnly=True)
    RequireArch(Cursor.ReadInts("<2I"), (5, 0), "initialized visual-state root fields")
    RequireArch(
        Cursor.ReadInts("<I"), (1,), "one standalone configuration relationship"
    )
    Configuration, Representation, Marker = Cursor.ReadInts("<iiI")
    RequireArch((Marker, Cursor.ReadInts("<I")), (1, (1,)), "one linked representation")
    RequireArch(
        Cursor.ReadInts("<i"), (Representation,), "same representation row identity"
    )
    Name = Cursor.ReadText()
    RequireArch(
        Cursor.ReadInts("<3i"),
        (Configuration, 0, 0),
        "unlinked representation configuration owner",
    )
    RequireArch(Cursor.ReadInts("<I"), (0,), "empty filtered component vector")
    (Count,) = Cursor.ReadInts("<I")
    RequireArch(1 <= Count <= 64, True, "bounded visual-state component-owner map")
    Materials, Displays, Owners = {}, {}, []
    for _ in range(Count):
        Feature, Created = ReadComponent(Cursor, Generation)
        RequireArch(
            Cursor.ReadInts("<IiI"),
            (1, Representation, 2),
            "owner representation and two attributes",
        )
        Material = ReadMaterial(Cursor, Generation, Materials)
        Display = ReadDisplay(Cursor, Displays)
        Owners.append(VisualOwner(Feature, Created, Material, Display))
    RequireArch(
        Cursor.ReadInts("<Ii"),
        (0, 0),
        "empty representation attributes and entity tracker",
    )
    RequireArch(Cursor.Offset, len(Data), "complete visual-state stream")
    State = VisualState(Configuration, Representation, Name, tuple(Owners))
    CheckVisualState(Generation, State)
    return State
