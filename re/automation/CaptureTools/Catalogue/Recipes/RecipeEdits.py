# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import nextafter

from CaptureTools.Catalogue.Recipes.RecipeProgram import RecipeProgram
from CaptureTools.Catalogue.Recipes.RecipeRules import RecipeRules


# dynamic edits stay legal for overridden radii angles and signed offsets rather than copying baseline values
def EditValue(ParamName, Parameters, Descriptor):
    Current = Parameters[ParamName]
    Lower, Upper = Descriptor["domains"][ParamName]
    if ParamName == "inner_radius_mm":
        Upper = min(Upper, nextafter(Parameters["outer_radius_mm"], Lower))
    elif ParamName == "outer_radius_mm":
        Lower = max(Lower, nextafter(Parameters["inner_radius_mm"], Upper))
    elif ParamName in ("angle1_deg", "angle2_deg"):
        Other = "angle2_deg" if ParamName == "angle1_deg" else "angle1_deg"
        Upper = min(Upper, 360 - Parameters[Other])
    Written = Descriptor["written_edit"]
    if (
        Written is not None
        and Written[0] == ParamName
        and Current == Descriptor["defaults"][ParamName]
        and Lower <= Written[1] <= Upper
    ):
        return float(Written[1])
    Candidate = Current + max(abs(Current) / 20, 0.001)
    if Candidate > Upper:
        Candidate = Current - max(abs(Current) / 20, 0.001)
    if Candidate < Lower:
        Candidate = Current + (Upper - Current) / 2
    if Candidate == Current or not Lower <= Candidate <= Upper:
        Candidate = Current - (Current - Lower) / 2
    if Candidate == Current or not Lower <= Candidate <= Upper:
        raise ValueError(
            f"recipe parameter {ParamName} has no distinct representable legal edit"
        )
    return float(Candidate)


# every declared driving control produces a fully recompiled independent native geometry challenge
def RecipeEdits(CaseValue, Descriptor):
    Edits = []
    for ParamName in CaseValue["parameters"]:
        Value = EditValue(ParamName, CaseValue["parameters"], Descriptor)
        Parameters = {**CaseValue["parameters"], ParamName: Value}
        Changed, _ = RecipeRules({**CaseValue, "parameters": Parameters})
        Edits.append(
            {
                "parameter": ParamName,
                "value": Value,
                "parameters": Changed["parameters"],
                "program": RecipeProgram(Changed, Descriptor),
            }
        )
    return Edits
