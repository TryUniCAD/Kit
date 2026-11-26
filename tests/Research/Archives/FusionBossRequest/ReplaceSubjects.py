# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as ReplaceValue

from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.Formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord


# observer controls must alter typed primary frames without replacing their entity groups
def ReplaceSubjects(
    Model: DocumentModel, Changes: dict[tuple[int, int], tuple[SubjectValue, ...]]
) -> DocumentModel:
    Segments: list[ParsedSegment] = []
    for Segment in Model.Segments:
        SegId = Segment.Metadata.Header.SegmentId
        Records: list[EntityRecord] = []
        for Record in Segment.Records:
            RecordKey = (SegId, Record.ObjectId)
            if Record.IsPrimary and RecordKey in Changes:
                Frame = ReplaceValue(Record.Frame, Subjects=Changes[RecordKey])
                Record = ReplaceValue(Record, Frame=Frame)
            Records.append(Record)
        Segments.append(ReplaceValue(Segment, Records=tuple(Records)))
    return ReplaceValue(Model, Segments=tuple(Segments))
