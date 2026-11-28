# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import CompletedProcess as ChildResult, run as RunProcess
from sys import executable as PythonExe

from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Inference.Authoring.Recipes.WriteRecipes import WriteRecipes


# the written recipe workflow must cross its actual command boundary with a real catalogue input
def RunCampaign(TmpPath: FilePath, Feature: str | None = None) -> ChildResult[str]:
    CataloguePath = WriteRecipes(TmpPath)
    if Feature is not None:
        Catalogue = DecodeJson(CataloguePath.read_bytes())
        for Family in Catalogue["families"]:
            Family["subfeatures"] = [
                Entry for Entry in Family["subfeatures"] if Entry["id"] == Feature
            ]
        Catalogue["families"] = [
            Family for Family in Catalogue["families"] if Family["subfeatures"]
        ]
        _ = CataloguePath.write_text(EncodeJson(Catalogue), encoding="utf-8")
    return RunProcess(
        [
            PythonExe,
            "-B",
            str(KRepoRoot / "re/automation/InferenceGrid/RunRecipeCampaign.py"),
            "--directory",
            str(TmpPath / "Campaign"),
            "--solidworks-catalogue",
            str(CataloguePath),
            "--prepare-only",
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
