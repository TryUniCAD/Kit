# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from argparse import ArgumentParser
from importlib import import_module as ImportModule
from typing import Callable, cast as CastValue
from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from sys import path as ImportPaths

# isolated probes must resolve research modules from the checkout under test
ImportPaths[:0] = [
    str(FilePath(__file__).resolve().parents[5] / "re/automation"),
    str(FilePath(__file__).resolve().parents[5]),
]

from tests.Research.Inference.Authoring.Contracts.CompiledCase import CompiledCase
from tests.Research.Inference.Authoring.Contracts.CaseFactory import CaseFactory
from tests.Research.Inference.Authoring.Contracts.ReadObject import ReadObject
from tests.Research.Inference.Authoring.Contracts.ReadText import ReadText
from tests.Research.Inference.Authoring.Contracts.SourcePin import SourcePin

# research compiler contracts remain explicit while their source stays outside production typing paths
KCompileRecipe = CastValue(
    Callable[[object], CompiledCase],
    getattr(
        ImportModule("CaptureTools.Catalogue.Recipes.CompileRecipe"), "CompileRecipe"
    ),
)

# source registry data stays inspectable without importing the research graph into static analysis
KRecipeBuilders = CastValue(
    dict[str, object],
    getattr(
        ImportModule("CaptureTools.Catalogue.Recipes.RecipeRegistry"), "KRecipeBuilders"
    ),
)

# saved native cases retain the trusted research validator at the actual process boundary
KValidateSolid = CastValue(
    Callable[[object], CompiledCase],
    getattr(
        ImportModule("CaptureTools.Catalogue.SolidWorks.ValidateSolid"), "ValidateSolid"
    ),
)

# geometry checks retain their real native measurement validation instead of a fixture substitute
KCheckSolidShape = CastValue(
    Callable[[object, object], None],
    getattr(
        ImportModule("CaptureTools.Catalogue.SolidWorks.CheckSolidShape"),
        "CheckSolidShape",
    ),
)

# source evidence remains bound to the actual checkout queried by the child process
KReadGit = CastValue(
    Callable[[FilePath, str, str], bytes], getattr(ImportModule("Corpus"), "git")
)

# research case creation preserves its keyword options through a dedicated callable contract
KMakeCase = CastValue(
    CaseFactory, getattr(ImportModule("InferenceGrid.Authoring.ReadCases"), "MakeCase")
)

# source manifests carry paths and hashes without widening checked research import roots
KReadSolidPins = CastValue(
    Callable[[str, object], list[SourcePin]],
    getattr(ImportModule("InferenceGrid.Authoring.SolidSources"), "ReadSolidPins"),
)

# controller summaries retain the original independent acceptance implementation across the import boundary
KAuthorOutcome = CastValue(
    Callable[[FilePath, object, object, list[object]], object],
    getattr(ImportModule("InferenceGrid.Authoring.AuthorOutcome"), "AuthorOutcome"),
)

# canonical case identity must use the same research digest as the native authoring tools
KCaseDigest = CastValue(
    Callable[[object], str], getattr(ImportModule("Records"), "digest")
)
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
    Payload = ReadObject(DecodeJson(Arguments.input.read_bytes()))
    Result: object
    if Arguments.action == "compile":
        Result = KCompileRecipe(Payload)
    elif Arguments.action == "registry":
        Result = KRecipeBuilders
    elif Arguments.action == "legacy":
        Result = {
            Recipe: KCaseDigest(KValidateSolid({"recipe": Recipe}))[:16]
            for Recipe in ("P01", "P02", "P03", "P04", "P05")
        }
    elif Arguments.action == "make":
        Result = KMakeCase(
            ReadText(Payload["application"]),
            ReadText(Payload["feature"]),
            Payload.get("overrides", {}),
            ReadText(Payload["mode"]),
            Required=True,
        )
    elif Arguments.action == "source":
        Revision = (
            KReadGit(FilePath(__file__).resolve().parents[5], "rev-parse", "HEAD")
            .decode("ascii")
            .strip()
        )
        Result = KReadSolidPins(Revision, Payload.get("source_root"))
    elif Arguments.action == "prism":
        CaseValue = (
            KCompileRecipe(
                {
                    "recipe": Payload["recipe"],
                    "parameters": Payload.get("parameters", {}),
                }
            )
            if Payload.get("compiled")
            else {**KValidateSolid({"recipe": "P03"}), "recipe": Payload["recipe"]}
        )
        KCheckSolidShape(CaseValue, ReadPrism())
        Result = {"verifier_returned": True, "fixture_only": True}
    elif Arguments.action == "outcome":
        Result = KAuthorOutcome(
            FilePath(ReadText(Payload["directory"])),
            Payload["plan"],
            Payload["submissions"],
            [],
        )
    else:
        Result = SubmitPlan(Payload)
    print(EncodeJson(Result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    MainRecipe()
