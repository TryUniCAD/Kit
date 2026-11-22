# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from CaptureTools.Catalogue.Recipes.CompileRecipe import CompileRecipe


# editing a case must discard the old derived program and recompute every geometry witness
def ProgramCase(CaseValue, Parameters=None, Options=None):
    if Parameters is not None and not isinstance(Parameters, dict):
        raise ValueError("recipe edit parameters must be a record")
    if Options is not None and not isinstance(Options, dict):
        raise ValueError("recipe edit options must be a record")
    Controls = {
        Key: Value
        for Key, Value in CaseValue.get("options", {}).items()
        if Key != "program"
    }
    return CompileRecipe(
        {
            "recipe": CaseValue["recipe"],
            "parameters": {**CaseValue.get("parameters", {}), **(Parameters or {})},
            "options": {**Controls, **(Options or {})},
        }
    )
