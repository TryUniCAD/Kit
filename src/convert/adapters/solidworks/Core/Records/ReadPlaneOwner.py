# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.solidworks.Container.Archive import (
    KDefinitionKind,
    ArchiveError,
    ReadTag,
)
from convert.adapters.solidworks.Container.PlaneBasis import KUnitRows, MatrixAxes
from convert.adapters.solidworks.Core.Records.NativeClass import NativeClass
from convert.adapters.solidworks.Core.Records.ReadLocalOwner import ReadLocalOwner
from convert.adapters.solidworks.Core.Records.ReadPlanePose import ReadPlanePose


# the origin supplies source owned unit and part identities without captured map indices
def ReadPlaneOwner(
    DataValue: bytes, Classes: tuple[NativeClass, ...], FeatureStart: int
) -> tuple[int, int, int] | None:
    Origins = tuple(
        Entry.offset
        for Entry in Classes
        if Entry.name == "moOriginProfileFeature_c" and Entry.offset < FeatureStart
    )
    if len(Origins) != 1:
        return None
    Records = tuple(
        Entry
        for Entry in Classes
        if Entry.name == "moCompRefPlane_c" and Origins[0] < Entry.offset < FeatureStart
    )
    if len(Records) != 1:
        return None
    try:
        TagValue = ReadTag(DataValue, Records[0].offset)
    except ArchiveError:
        return None
    if (TagValue.kind, TagValue.schema, TagValue.class_name, TagValue.wide) != (
        KDefinitionKind,
        1,
        "moCompRefPlane_c",
        False,
    ):
        return None
    LocalValue = ReadLocalOwner(
        DataValue, Records[0].offset + TagValue.size, FeatureStart
    )
    if LocalValue is None:
        return None
    Generation, UnitIndex, PartIndex, ReferenceOffset = LocalValue
    OwnerValue = Generation, UnitIndex, PartIndex
    PoseValue = ReadPlanePose(
        DataValue,
        ReferenceOffset,
        FeatureStart,
        OwnerValue,
        Records[0].offset + TagValue.size,
    )
    if PoseValue != (2, 3, MatrixAxes(KUnitRows), None):
        return None
    return OwnerValue
