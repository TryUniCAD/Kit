# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# independent journal comparison prevents retired fixture values from becoming qualification reserves again
def CheckReserves(Retired: dict, Revised: dict) -> None:
    assert Revised["reservations"][0] == Retired["reservations"][0]
    assert Revised["reservations"][-1]["status"] == "frozen"
    UsedValues = {
        CaseValue[FieldName]
        for CaseValue in Retired["reservations"][0]["cases"]
        for FieldName in ("offset_mm", "edit_mm")
    }
    FreshValues = {
        CaseValue[FieldName]
        for CaseValue in Revised["reservations"][-1]["cases"]
        for FieldName in ("offset_mm", "edit_mm")
    }
    assert UsedValues.isdisjoint(FreshValues)
    assert Revised["registration"] is None
