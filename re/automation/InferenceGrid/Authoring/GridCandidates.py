# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from CaptureTools.Catalogue.Recipes.RecipeRegistry import KRecipeBuilders


# legal parameter ladders must still exist near coupled radius and angle boundaries
def GridCandidates(CaseValue, ParamName):
    Current = CaseValue["parameters"][ParamName]
    if Current == 0:
        yield from (1.0, -1.0, 0.1, -0.1, 10.0, -10.0)
    else:
        for Factor in (0.7, 1.3, 0.85, 1.15, 0.5, 1.5):
            yield Current * Factor
    Descriptor = KRecipeBuilders.get(CaseValue["recipe"])
    Bounds = (
        Descriptor["domains"][ParamName]
        if Descriptor is not None
        else (0.0, max(abs(Current), 1.0) * 2)
    )
    for StepValue in range(1, 55):
        for Bound in Bounds:
            yield Current + (Bound - Current) * (2.0**-StepValue)
