# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from InferenceGrid.MeasureBodies import near


def parameter_witness(decoded, measured):
    actual = {row["name"]: row for row in decoded if isinstance(row.get("name"), str) and row["name"]}
    expected = {row["name"]: row for row in measured if isinstance(row.get("name"), str) and row["name"]}
    same = len(actual) == len(decoded) == len(expected) == len(measured) and actual.keys() == expected.keys()
    checks = {}
    for name in sorted(actual.keys() & expected.keys()):
        row = expected[name]
        checks[name] = {key: actual[name][key] == row[key] for key in ("expression", "unit", "role") if key in row}
        if "value" in row:
            checks[name]["value"] = near(actual[name]["value"], row["value"], 1e-9)
    return {"all_names_match": same, "fields": checks, "native_count": len(decoded), "measured_count": len(measured)}
