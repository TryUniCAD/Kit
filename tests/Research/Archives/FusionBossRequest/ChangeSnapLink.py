# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as ReplaceValue

from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


# scope mutations must preserve the record frame and every unrelated native field
def ChangeSnapLink(Record: EntityRecord, LinkValue: KEntityValue) -> EntityRecord:
    Groups = tuple(
        ReplaceValue(
            Group,
            Fields=tuple(
                (
                    ReplaceValue(FieldValue, Value=LinkValue)
                    if FieldValue.FieldName == "toolbodyCaches"
                    else FieldValue
                )
                for FieldValue in Group.Fields
            ),
        )
        for Group in Record.Groups
    )
    return ReplaceValue(Record, Groups=Groups)
