# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps

from CaptureTools.Catalogue.Recipes.RecipeEdits import RecipeEdits
from CaptureTools.Catalogue.Recipes.RecipeProgram import RecipeProgram
from CaptureTools.Catalogue.Recipes.RecipeRows import RecipeHash
from CaptureTools.Catalogue.Recipes.RecipeRules import RecipeRules
from CaptureTools.Catalogue.Recipes.RecipeVariants import RecipeVariants


# native programs are reproducible typed consequences of exact recipes and cannot be supplied as executable overrides
def CompileRecipe(CaseValue):
    Normal, Descriptor = RecipeRules(CaseValue)
    if RecipeHash(Normal["recipe"]) != Descriptor["written_recipe_sha256"]:
        raise ValueError(
            "written recipe source changed without reviewed executable binding"
        )
    Program = RecipeProgram(Normal, Descriptor)
    Program["edits"] = RecipeEdits(Normal, Descriptor)
    Program["variants"] = RecipeVariants(Normal, Descriptor)
    Supplied = CaseValue.get("options", {})
    if "program" in Supplied and dumps(
        Supplied["program"],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ) != dumps(
        Program,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ):
        raise ValueError(
            "reserved compiled program differs from exact recipe recomputation"
        )
    return {**Normal, "options": {**Normal["options"], "program": Program}}


# callers share one canonical validator rather than maintaining competing normalization rules
NormalizeRecipe = CompileRecipe
