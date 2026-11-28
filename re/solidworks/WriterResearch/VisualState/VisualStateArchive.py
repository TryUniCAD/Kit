# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from CmgrVisualBody import WriteCmgrVisualBody
from PartArchive import PartArchiveWriter
from VisualState.VisualStateModel import (
    CheckVisualState,
    KAppearanceClass,
    KDisplayClass,
    KFeatureClass,
    KHolderClass,
    KMaterialClass,
    KUnitClass,
    KVisualRootClass,
)


def BeginVisualObject(Writer, Name):
    Index = Writer.next_index + int(Name not in Writer.classes)
    Writer.BeginObject(Name, 1)
    return Index


def WriteComponent(Writer, Generation, Owner):
    BeginVisualObject(
        Writer, KHolderClass if Owner.FeatureId is None else KFeatureClass
    )
    BeginVisualObject(Writer, KUnitClass)
    Writer.u16(0)
    Writer.u8(0)
    for _ in range(6):
        Writer.i32(0)
    Writer.i32(0)
    Writer.i32(0)
    Writer.u32(0)
    Writer.i32(0)
    for _ in range(4):
        Writer.i32(-1)
    for _ in range(5):
        Writer.i32(0)
    Writer.u32(Generation)
    if Owner.FeatureId is not None:
        Writer.i32(Owner.FeatureId)
        Writer.u32(Owner.Created)


def WriteMaterial(Writer, Generation, Fields, Cache):
    if Fields in Cache:
        Writer.ReferenceObject(Cache[Fields], KMaterialClass)
        return
    Cache[Fields] = BeginVisualObject(Writer, KMaterialClass)
    Writer.u32(1)
    if Fields is None:
        Writer.u16(0)
        return
    BeginVisualObject(Writer, KAppearanceClass)
    WriteCmgrVisualBody(Writer, Generation, Fields, AllowSystemTexture=True)


def WriteDisplay(Writer, Display, Cache):
    if Display in Cache:
        Writer.ReferenceObject(Cache[Display], KDisplayClass)
        return
    Cache[Display] = BeginVisualObject(Writer, KDisplayClass)
    Writer.u32(1)
    Writer.i32(int(Display.Visible))
    Writer.i32(Display.DisplayMode)
    Writer.i32(Display.EdgesInShadedMode)
    Writer.i32(Display.HlrDisplayQuality)


def EncodeVisualState(Generation, State):
    CheckVisualState(Generation, State)
    Writer = PartArchiveWriter()
    Writer.u32(Generation)
    Writer.i32(0)
    BeginVisualObject(Writer, KVisualRootClass)
    Writer.u32(5)
    Writer.u32(0)
    Writer.u32(1)
    Writer.i32(State.ConfigurationId)
    Writer.i32(State.RepresentationId)
    Writer.u32(1)
    Writer.u32(1)
    Writer.i32(State.RepresentationId)
    Writer.string(State.Name)
    Writer.i32(State.ConfigurationId)
    Writer.i32(0)
    Writer.i32(0)
    Writer.u32(0)
    Writer.u32(len(State.Owners))
    Materials, Displays = {}, {}
    for Owner in State.Owners:
        WriteComponent(Writer, Generation, Owner)
        Writer.u32(1)
        Writer.i32(State.RepresentationId)
        Writer.u32(2)
        WriteMaterial(Writer, Generation, Owner.Material, Materials)
        WriteDisplay(Writer, Owner.Display, Displays)
    Writer.u32(0)
    Writer.i32(0)
    return Writer.build()
