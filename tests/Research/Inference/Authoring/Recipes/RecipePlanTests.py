# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath

from pytest import mark as CaseMark

from tests.Research.Inference.Authoring.Recipes.LegacyCases import KLegacyCases
from tests.Research.Inference.Authoring.Recipes.RecipeTargets import KRecipeTargets
from tests.Research.Inference.Authoring.Recipes.RunCatalogue import RunCatalogue


# named authoring remains restricted to exact registered recipes and their reserved evidence modes
@CaseMark.parametrize("ModeValue", ("discovery", "qualification", "holdout"))
def CheckPlanModes(TmpPath: FilePath, ModeValue: str) -> None:
    Process = RunCatalogue(TmpPath, "--capture-mode", ModeValue)
    assert Process.returncode == 0, Process.stdout + Process.stderr
    PlanValue = DecodeJson((TmpPath / "Run/AuthoringPlan.json").read_bytes())
    Samples = [Entry["case"] for Entry in PlanValue["samples"].values()]
    Expected = {
        "discovery": {"P01", "P03", "P04"},
        "qualification": {"P02"},
        "holdout": {"P05"},
    }[ModeValue]
    Prefix = {
        "discovery": "extrude-",
        "qualification": "never-",
        "holdout": "revolve-",
    }[ModeValue]
    Expected |= {Recipe for Recipe in KRecipeTargets if Recipe.startswith(Prefix)}
    assert {Entry["recipe"] for Entry in Samples} == Expected
    for Entry in Samples:
        if Entry["recipe"] in KLegacyCases:
            assert Entry["id"] == KLegacyCases[Entry["recipe"]]
    Features = PlanValue["features"]["solidworks"]
    assert (
        Features["family:extrude:surface-extrude"]["status"]
        == "authoring_recipe_unavailable"
    )
    assert (
        Features["family:revolve:surface-revolve"]["status"]
        == "authoring_recipe_unavailable"
    )
    assert (
        Features["family:fillet:constant-radius-fillet"]["status"]
        == "authoring_recipe_unavailable"
    )
    Result = DecodeJson((TmpPath / "Run/CatalogueResult.json").read_bytes())
    assert Result["status"] == "prepared"
    assert not (TmpPath / "Run/Store").exists()


# identical aliases reuse observations while distinct requested values retain separate immutable cases
def CheckPlanCases(TmpPath: FilePath) -> None:
    Cases = [
        {
            "application": "solidworks",
            "feature": KRecipeTargets["extrude-offset-start"],
            "parameters": {"offset_mm": Offset},
        }
        for Offset in (7, 7, 11)
    ]
    Cases += [
        {"application": "solidworks", "feature": Feature}
        for Feature in (
            "family:sketchlines:corner-rectangle",
            "family:sketchdimensions:linear-dimension",
        )
    ]
    CasePath = TmpPath / "Cases.json"
    _ = CasePath.write_text(
        EncodeJson({"schema_version": 1, "cases": Cases}), encoding="utf-8"
    )
    Process = RunCatalogue(TmpPath, "--authoring-cases", CasePath)
    assert Process.returncode == 0, Process.stdout + Process.stderr
    PlanValue = DecodeJson((TmpPath / "Run/AuthoringPlan.json").read_bytes())
    assert len(PlanValue["samples"]) == 3
    Samples = [Entry["case"] for Entry in PlanValue["samples"].values()]
    assert {
        Entry["parameters"]["offset_mm"]
        for Entry in Samples
        if Entry["recipe"] == "extrude-offset-start"
    } == {7, 11}
    Features = PlanValue["features"]["solidworks"]
    assert (
        Features["family:sketchlines:corner-rectangle"]["samples"]
        == Features["family:sketchdimensions:linear-dimension"]["samples"]
    )
    assert Features["family:extrude:surface-extrude"]["status"] == "not_selected"
    assert not (TmpPath / "Run/Store").exists()


# explicit requests cannot promote unsupported recipes or consume reserved families through capture preparation
@CaseMark.parametrize(
    "Feature,ModeValue",
    (
        ("family:extrude:surface-extrude", "discovery"),
        (KRecipeTargets["revolve-thin"], "discovery"),
        (KRecipeTargets["extrude-midplane"], "holdout"),
        ("family:extrude:invented", "discovery"),
    ),
)
def CheckPlanRefuse(TmpPath: FilePath, Feature: str, ModeValue: str) -> None:
    CasePath = TmpPath / "Cases.json"
    _ = CasePath.write_text(
        EncodeJson(
            {
                "schema_version": 1,
                "cases": [{"application": "solidworks", "feature": Feature}],
            }
        ),
        encoding="utf-8",
    )
    Process = RunCatalogue(
        TmpPath, "--capture-mode", ModeValue, "--authoring-cases", CasePath
    )
    assert Process.returncode == 1
    assert "refused" in Process.stderr
    assert not (TmpPath / "Run").exists()
