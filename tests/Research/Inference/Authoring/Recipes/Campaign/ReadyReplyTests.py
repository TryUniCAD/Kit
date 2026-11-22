# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath

from tests.Research.Inference.Authoring.Recipes.Campaign.RunCampaign import RunCampaign


# an assistant readiness message cannot replace an executable binding or measured native evidence
def CheckReadyReply(TmpPath: FilePath) -> None:
    Feature = "family:extrude:surface-extrude"
    Prepared = RunCampaign(TmpPath, Feature)
    assert Prepared.returncode == 0, Prepared.stdout + Prepared.stderr
    NextRecipe = DecodeJson((TmpPath / "Campaign/NextRecipe.json").read_bytes())
    ReplyPath = FilePath(NextRecipe["reply_path"])
    assert ReplyPath == TmpPath / "Campaign/RecipeReply.json"
    _ = ReplyPath.write_text(
        EncodeJson(
            {
                "key": NextRecipe["key"],
                "recipe_sha256": NextRecipe["recipe_sha256"],
                "status": "ready",
                "reason": "assistant says the executor is ready",
            }
        ),
        encoding="utf-8",
    )
    Continued = RunCampaign(TmpPath, Feature)
    assert Continued.returncode == 0, Continued.stdout + Continued.stderr
    State = DecodeJson((TmpPath / "Campaign/Campaign.json").read_bytes())
    assert len(State["entries"]) == 1
    Entry = State["entries"][NextRecipe["key"]]
    assert Entry["native_verified"] is False
    assert Entry["needs_assistant"] is True
    assert Entry["assistant_error"]
    assert Entry["row_sha256"] == NextRecipe["recipe_sha256"]
    assert all(
        Attempt.get("native_verified") is not True for Attempt in Entry["attempts"]
    )
    assert not any(
        EntryPath.suffix.lower() in {".sldprt", ".f3d"}
        for EntryPath in TmpPath.rglob("*")
    )
