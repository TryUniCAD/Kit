# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from InferenceGrid.Authoring.ReadCases import MakeCase
from InferenceGrid.Authoring.GridCandidates import GridCandidates
from math import isfinite


# parameter ladders vary one driving quantity while keeping every other native input fixed
def ExpandCaseGrid(Selected, ModeValue, GridValue):
    if GridValue == "baseline":
        return Selected
    if GridValue != "three-values":
        raise ValueError("unknown authoring parameter grid")
    Expanded = []
    for Selection in Selected:
        Expanded.append(Selection)
        CaseValue = Selection["case"]
        Options = {
            NameValue: Value
            for NameValue, Value in CaseValue["options"].items()
            if NameValue != "program"
        }
        for NameValue, Original in sorted(CaseValue["parameters"].items()):
            Accepted = {Original}
            for Changed in GridCandidates(CaseValue, NameValue):
                if not isfinite(Changed) or Changed in Accepted:
                    continue
                try:
                    Candidate = MakeCase(
                        Selection["application"],
                        Selection["feature"],
                        {
                            "parameters": {
                                **CaseValue["parameters"],
                                NameValue: Changed,
                            },
                            "options": Options,
                        },
                        ModeValue,
                        Required=True,
                    )
                except ValueError:
                    continue
                Expanded.append(Candidate)
                Accepted.add(Changed)
                if len(Accepted) == 3:
                    break
            if len(Accepted) != 3:
                raise ValueError(
                    f"cannot construct three legal values for {CaseValue['recipe']} {NameValue}"
                )
    return Expanded
