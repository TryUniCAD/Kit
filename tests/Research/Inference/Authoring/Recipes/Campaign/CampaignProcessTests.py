# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Inference.Authoring.Recipes.Campaign.RunCampaign import RunCampaign


# preparation must expose every written recipe including missing executors and preserve stable progress on repetition
def CheckWritten(TmpPath: FilePath) -> None:
    Process = RunCampaign(TmpPath)
    assert Process.returncode == 0, Process.stdout + Process.stderr
    StatePath = TmpPath / "Campaign/Campaign.json"
    State = DecodeJson(StatePath.read_bytes())
    Catalogue = DecodeJson((TmpPath / "FeaturePlan.json").read_bytes())
    Features = {
        Entry["id"]
        for Family in Catalogue["families"]
        for Entry in Family["subfeatures"]
    }
    Written = DecodeJson(
        (KRepoRoot / "re/automation/FeatureRecipeSpecs.json").read_bytes()
    )["recipes"]
    Expected = {
        Entry["id"]
        for Entry in Written
        if set(Entry["entries"].get("solidworks", [])) & Features
    }
    assert len(Expected) == len(State["entries"]) == 17
    assert {Entry["recipe_id"] for Entry in State["entries"].values()} == Expected
    assert any(
        Entry["recipe_id"] == "extrude-surface" and Entry["needs_assistant"]
        for Entry in State["entries"].values()
    )
    NextPath = TmpPath / "Campaign/NextRecipe.json"
    NextRecipe = DecodeJson(NextPath.read_bytes())
    assert (
        NextRecipe["recipe_sha256"] == State["entries"][NextRecipe["key"]]["row_sha256"]
    )
    assert NextRecipe["recipe"] == State["entries"][NextRecipe["key"]]["recipe"]
    Repeated = RunCampaign(TmpPath)
    assert Repeated.returncode == 0, Repeated.stdout + Repeated.stderr
    Again = DecodeJson(StatePath.read_bytes())
    assert Again["entries"] == State["entries"]
    assert (
        DecodeJson(NextPath.read_bytes())["recipe_sha256"]
        == NextRecipe["recipe_sha256"]
    )
    assert all(Entry["native_verified"] is False for Entry in Again["entries"].values())
