# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from CaptureTools.Catalogue.Fusion.FusionBatch import ModelCase
from CaptureTools.Catalogue.Fusion.FusionParams import ValidateFusion


# every editable driving parameter needs a distinct legal native geometry challenge
def EditCases(Case):
    Normal = ValidateFusion(ModelCase(Case))
    Original = Normal["parameters"]
    Edits = []
    for ParamName, ParamValue in Original.items():
        if ParamName == "angle_deg":
            Value = ParamValue + (360 - ParamValue) / 10 if ParamValue < 360 else 330.0
        elif ParamName == "inner_radius_mm":
            Value = ParamValue + (Original["outer_radius_mm"] - ParamValue) / 10
        elif ParamName.startswith("cut_"):
            Owner = ParamName.removeprefix("cut_")
            Value = ParamValue + (Original[Owner] - ParamValue) / 10
        else:
            Lower = Original.get("cut_" + ParamName, 0)
            if ParamName == "outer_radius_mm":
                Lower = Original["inner_radius_mm"]
            Value = (
                ParamValue * 1.05 if ParamValue <= 95000 else (ParamValue + Lower) / 2
            )
        Parameters = {**Original, ParamName: Value}
        Changed = ValidateFusion({**Normal, "parameters": Parameters})
        Edits.append({"parameter": ParamName, "value": Value, "case": Changed})
    return Edits
