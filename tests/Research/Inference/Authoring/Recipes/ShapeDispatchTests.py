# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath

from pytest import mark as CaseMark

from tests.Research.Inference.Authoring.Recipes.RunProbe import RunProbe


# correct prism mass properties cannot qualify an unknown recipe through a generic geometry fallback
@CaseMark.parametrize(
    "RecipeKey", ("invented-prism", "extrude-surface", "extrude-midplane")
)
def CheckNoPrism(TmpPath: FilePath, RecipeKey: str) -> None:
    Process = RunProbe(TmpPath, "prism", {"recipe": RecipeKey})
    assert Process.returncode != 0
    assert "ValueError" in Process.stderr
    assert not Process.stdout.strip()


# matching body mass properties cannot substitute for the required native measurement schema
def CheckMassOnly(TmpPath: FilePath) -> None:
    Process = RunProbe(
        TmpPath,
        "prism",
        {
            "recipe": "extrude-offset-start",
            "parameters": {"offset_mm": 0},
            "compiled": True,
        },
    )
    assert Process.returncode != 0
    assert "surface_body_count" in Process.stderr
    assert not Process.stdout.strip()
