# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from argparse import ArgumentParser
from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from sys import path as ImportPaths

# isolated probes must resolve research modules from the checkout under test
ImportPaths[:0] = [
    str(FilePath(__file__).resolve().parents[5] / "re/automation"),
    str(FilePath(__file__).resolve().parents[5]),
]

from CaptureTools.Catalogue.Recipes.CompileRecipe import CompileRecipe
from CaptureTools.Catalogue.Recipes.RecipeRegistry import KRecipeBuilders
from CaptureTools.Catalogue.SolidWorks.ValidateSolid import ValidateSolid
from CaptureTools.Catalogue.SolidWorks.CheckSolidShape import CheckSolidShape
from Corpus import git as ReadGit
from InferenceGrid.Authoring.ReadCases import MakeCase
from InferenceGrid.Authoring.SolidSources import ReadSolidPins
from InferenceGrid.Authoring.AuthorOutcome import AuthorOutcome
from Records import digest as CaseDigest
from tests.Research.Inference.Authoring.Recipes.ReadPrism import ReadPrism
from tests.Research.Inference.Authoring.Recipes.SubmitPlan import SubmitPlan


# public research inputs cross an interpreter boundary without loading any native automation entry point
def MainRecipe() -> None:
    Parser = ArgumentParser(allow_abbrev=False)
    _ = Parser.add_argument(
        "action",
        choices=(
            "compile",
            "registry",
            "legacy",
            "make",
            "source",
            "prism",
            "outcome",
            "submit",
        ),
    )
    _ = Parser.add_argument("input", type=FilePath)
    Arguments = Parser.parse_args()
    Payload = DecodeJson(Arguments.input.read_bytes())
    if Arguments.action == "compile":
        Result = CompileRecipe(Payload)
    elif Arguments.action == "registry":
        Result = KRecipeBuilders
    elif Arguments.action == "legacy":
        Result = {
            Recipe: CaseDigest(ValidateSolid({"recipe": Recipe}))[:16]
            for Recipe in ("P01", "P02", "P03", "P04", "P05")
        }
    elif Arguments.action == "make":
        Result = MakeCase(
            Payload["application"],
            Payload["feature"],
            Payload.get("overrides", {}),
            Payload["mode"],
            Required=True,
        )
    elif Arguments.action == "source":
        Revision = (
            ReadGit(FilePath(__file__).resolve().parents[5], "rev-parse", "HEAD")
            .decode("ascii")
            .strip()
        )
        Result = ReadSolidPins(Revision, Payload.get("source_root"))
    elif Arguments.action == "prism":
        CaseValue = (
            CompileRecipe(
                {
                    "recipe": Payload["recipe"],
                    "parameters": Payload.get("parameters", {}),
                }
            )
            if Payload.get("compiled")
            else {**ValidateSolid({"recipe": "P03"}), "recipe": Payload["recipe"]}
        )
        CheckSolidShape(CaseValue, ReadPrism())
        Result = {"verifier_returned": True, "fixture_only": True}
    elif Arguments.action == "outcome":
        Result = AuthorOutcome(
            FilePath(Payload["directory"]), Payload["plan"], Payload["submissions"], []
        )
    else:
        Result = SubmitPlan(Payload)
    print(EncodeJson(Result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    MainRecipe()
