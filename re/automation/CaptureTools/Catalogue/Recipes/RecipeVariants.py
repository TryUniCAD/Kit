# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from CaptureTools.Catalogue.Recipes.RecipeProgram import RecipeProgram
from CaptureTools.Catalogue.Recipes.RecipeRules import RecipeRules


# only executable reviewed variation identifiers can extend native capture work
def RecipeVariants(CaseValue, Descriptor):
    Variants = []
    for VariantName in Descriptor["supported_variants"]:
        Options = dict(CaseValue["options"])
        if VariantName.startswith("basis-"):
            Options["basis"] = VariantName.removeprefix("basis-").upper()
        elif VariantName == "direction-negative":
            Options["direction"] = -1
        else:
            Options["variant"] = VariantName
        if Options == CaseValue["options"]:
            continue
        Changed, _ = RecipeRules({**CaseValue, "options": Options})
        Variants.append(
            {
                "name": VariantName,
                "parameters": Changed["parameters"],
                "options": Changed["options"],
                "program": RecipeProgram(Changed, Descriptor),
            }
        )
    return Variants
