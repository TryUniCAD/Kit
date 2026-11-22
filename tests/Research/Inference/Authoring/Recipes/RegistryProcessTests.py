# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath

from pytest import mark as CaseMark

from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Inference.Authoring.Recipes.LegacyCases import KLegacyCases
from tests.Research.Inference.Authoring.Recipes.RecipeTargets import KRecipeTargets
from tests.Research.Inference.Authoring.Recipes.RunProbe import RunProbe


# descriptor source bindings must identify exact written recipes rather than broad taxonomy families
def CheckRegistry(TmpPath: FilePath) -> None:
    Process = RunProbe(TmpPath, "registry", {})
    assert Process.returncode == 0, Process.stderr
    Registry = DecodeJson(Process.stdout)
    assert set(Registry) == set(KRecipeTargets)
    Written = DecodeJson(
        (KRepoRoot / "re/automation/FeatureRecipeSpecs.json").read_bytes()
    )
    Recipes = {Entry["id"]: Entry for Entry in Written["recipes"]}
    for Recipe, Descriptor in Registry.items():
        Source = EncodeJson(
            Recipes[Recipe],
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        assert Descriptor["written_recipe_sha256"] == HashBytes(Source).hexdigest()
        assert Descriptor["applications"] == ["solidworks"]
        assert Descriptor["modes"] == (
            ["discovery"] if Recipe.startswith("extrude-") else ["holdout"]
        )
        assert (
            set(Descriptor["defaults"])
            == set(Descriptor["native_fields"])
            == set(Descriptor["units"])
            == set(Descriptor["domains"])
        )
        assert not set(Descriptor["supported_variants"]) & set(
            Descriptor["unsupported_variants"]
        )


# the five reviewed baseline identities must remain unchanged when no expansion option is selected
def CheckLegacyIds(TmpPath: FilePath) -> None:
    Process = RunProbe(TmpPath, "legacy", {})
    assert Process.returncode == 0, Process.stderr
    assert DecodeJson(Process.stdout) == KLegacyCases


# a written entry owned by another application cannot authorize native authoring through a registry alias
@CaseMark.parametrize(
    "Application,Feature,ModeValue",
    (
        ("fusion", KRecipeTargets["extrude-midplane"], "discovery"),
        ("solidworks", "api:adsk.fusion.ExtrudeFeature", "discovery"),
        ("fusion", "family:sketchlines:corner-rectangle", "discovery"),
    ),
)
def CheckAppGate(
    TmpPath: FilePath, Application: str, Feature: str, ModeValue: str
) -> None:
    Process = RunProbe(
        TmpPath,
        "make",
        {"application": Application, "feature": Feature, "mode": ModeValue},
    )
    assert Process.returncode != 0
    assert "requested application" in Process.stderr
