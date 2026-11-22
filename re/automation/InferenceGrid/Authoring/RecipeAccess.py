# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from CaptureTools.Catalogue.Recipes.RecipeRegistry import KRecipeBuilders


# written instructions cannot grant execution without an explicit application and evidence mode binding
def CanBuildRecipe(Application, Written, ModeValue):
    if Written is None or not Written.get("entries", {}).get(Application):
        return False
    Builder = KRecipeBuilders.get(Written["id"])
    return (
        Builder is not None
        and Application in Builder["applications"]
        and ModeValue in Builder["modes"]
    )
