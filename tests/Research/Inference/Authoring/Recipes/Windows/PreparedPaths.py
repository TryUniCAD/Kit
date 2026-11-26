# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from tests.Research.Inference.Authoring.Contracts.CompiledCase import CompiledCase


# the emitted program roster defines the native archive names that the application will later save
def PreparedPaths(CaseValue: CompiledCase, OutputPath: FilePath) -> list[FilePath]:
    RecipeKey = CaseValue["recipe"]
    Program = CaseValue["options"]["program"]
    Suffixes = ["baseline-a", "baseline-b"]
    Suffixes += [
        "edit-" + Entry["parameter"] + "-" + format(Entry["value"], ".17g")
        for Entry in Program["edits"]
    ]
    Suffixes += [Entry["name"] for Entry in Program["variants"]]
    return [
        OutputPath / RecipeKey / (RecipeKey + "-solidworks-" + Suffix + ".SLDPRT")
        for Suffix in Suffixes
    ]
