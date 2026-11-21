# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath
from tests.Research.Inference.BuilderDevelopment.RunBuilder import RunBuilder
from tests.Research.Inference.Authoring.Recipes.WriteRecipes import WriteRecipes


# adding automatic development must preserve the existing opt out command behavior
def CheckDisabled(TmpPath: FilePath) -> None:
    _ = WriteRecipes(TmpPath)
    Process = RunBuilder(TmpPath, IsAuto=False)
    assert Process.returncode == 0, Process.stdout + Process.stderr
    Campaign = DecodeJson((TmpPath / "Run/Campaign.json").read_bytes())
    assert len(Campaign["entries"]) == 17
    assert not (TmpPath / "Run/BuilderJob.json").exists()
    assert not (TmpPath / "Run/ModelBudget.json").exists()
