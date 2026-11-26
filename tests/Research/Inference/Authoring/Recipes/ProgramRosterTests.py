# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath

from pytest import mark as CaseMark

from tests.Research.Inference.Authoring.Recipes.RecipeTargets import KRecipeTargets
from tests.Research.Inference.Authoring.Recipes.RunProbe import RunProbe


# every exposed dimension must have an independent legal edit rather than a copied baseline challenge
@CaseMark.parametrize("RecipeKey", tuple(KRecipeTargets))
def CheckEditRoster(TmpPath: FilePath, RecipeKey: str) -> None:
    Process = RunProbe(TmpPath, "compile", {"recipe": RecipeKey})
    assert Process.returncode == 0, Process.stderr
    Compiled = DecodeJson(Process.stdout)
    Program = Compiled["options"]["program"]
    assert {Entry["parameter"] for Entry in Program["edits"]} == set(
        Compiled["parameters"]
    )
    assert len(Program["edits"]) == len(Compiled["parameters"])
    for Entry in Program["edits"]:
        Changes = {
            ParamName
            for ParamName, Value in Entry["parameters"].items()
            if Value != Compiled["parameters"][ParamName]
        }
        assert Changes == {Entry["parameter"]}
        assert Entry["parameters"][Entry["parameter"]] == Entry["value"]
        Edited = RunProbe(
            TmpPath, "compile", {"recipe": RecipeKey, "parameters": Entry["parameters"]}
        )
        assert Edited.returncode == 0, Edited.stderr
        Recompiled = DecodeJson(Edited.stdout)["options"]["program"]
        assert {
            Field: Value
            for Field, Value in Recompiled.items()
            if Field not in {"edits", "variants"}
        } == Entry["program"]


# declared variations must form explicit recompilable requests with unsupported written variations absent
@CaseMark.parametrize("RecipeKey", tuple(KRecipeTargets))
def CheckVariants(TmpPath: FilePath, RecipeKey: str) -> None:
    Process = RunProbe(TmpPath, "compile", {"recipe": RecipeKey})
    assert Process.returncode == 0, Process.stderr
    Program = DecodeJson(Process.stdout)["options"]["program"]
    Expected = {"units-inch"}
    if RecipeKey.startswith("extrude-"):
        Expected |= {"basis-yz", "basis-xz"}
    if RecipeKey in {"extrude-two-direction", "extrude-offset-start", "extrude-thin"}:
        Expected.add("direction-negative")
    if RecipeKey == "extrude-thin":
        Expected.add("midplane-wall")
    assert {Entry["name"] for Entry in Program["variants"]} == Expected
    for Entry in Program["variants"]:
        Variant = RunProbe(
            TmpPath,
            "compile",
            {
                "recipe": RecipeKey,
                "parameters": Entry["parameters"],
                "options": Entry["options"],
            },
        )
        assert Variant.returncode == 0, Variant.stderr
        Recompiled = DecodeJson(Variant.stdout)["options"]["program"]
        assert {
            Field: Value
            for Field, Value in Recompiled.items()
            if Field not in {"edits", "variants"}
        } == Entry["program"]
