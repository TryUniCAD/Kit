# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping
from typing import cast as CastValue
from tests.Research.Inference.BuilderDevelopment.Contracts.ReadRecord import ReadRecord
from tests.Research.Inference.BuilderDevelopment.Contracts.ReadItems import ReadItems


# independent journal comparison prevents retired fixture values from becoming qualification reserves again
def CheckReserves(Retired: Mapping[str, object], Revised: Mapping[str, object]) -> None:
    OldCases = [ReadRecord(Value) for Value in ReadItems(Retired["reservations"])]
    NewCases = [ReadRecord(Value) for Value in ReadItems(Revised["reservations"])]
    assert NewCases[0] == OldCases[0]
    assert NewCases[-1]["status"] == "frozen"
    UsedValues = {
        CastValue(float, CaseValue[FieldName])
        for CaseValue in [
            ReadRecord(Value) for Value in ReadItems(OldCases[0]["cases"])
        ]
        for FieldName in ("offset_mm", "edit_mm")
    }
    FreshValues = {
        CastValue(float, CaseValue[FieldName])
        for CaseValue in [
            ReadRecord(Value) for Value in ReadItems(NewCases[-1]["cases"])
        ]
        for FieldName in ("offset_mm", "edit_mm")
    }
    assert UsedValues.isdisjoint(FreshValues)
    assert Revised["registration"] is None
