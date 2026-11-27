# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from argparse import ArgumentParser
from json import dumps, loads
from pathlib import Path
from subprocess import run
from sys import argv, executable, path
from time import monotonic, sleep

path[:0] = [
    str(Path(__file__).resolve().parents[1]),
    str(Path(__file__).resolve().parents[3] / "src"),
]

from InferenceGrid.FeatureCatalogue import ReadCatalogue
from InferenceGrid.FeatureFusionCatalogue import ReadFusionCatalogue
from InferenceGrid.RecipeCampaign.ApplyRecipe import ApplyRecipe
from InferenceGrid.RecipeCampaign.CampaignState import (
    MergePlan,
    ReadReply,
    Summarize,
    WriteNext,
    WriteState,
)
from InferenceGrid.RecipeCampaign.RecipePlan import PlanRecipes
from InferenceGrid.CatalogueRuntime import HoldCatalogue
from InferenceGrid.BuilderDevelopment.Options import (
    AddBuilderOptions,
    CheckBuilderOptions,
)


# one entry point walks written recipes and exposes unresolved work to its assisting agent
def ReadOptions():
    Parser = ArgumentParser(
        description="Apply catalogue recipes with a persistent assistant handoff",
        allow_abbrev=False,
    )
    Parser.add_argument("--directory", type=Path, required=True)
    Parser.add_argument("--solidworks-catalogue", type=Path)
    Parser.add_argument("--fusion-catalogue", type=Path)
    Parser.add_argument("--solidworks-host", type=Path)
    Parser.add_argument("--native-config", type=Path)
    Parser.add_argument("--native-kind")
    Parser.add_argument("--native-resource")
    Parser.add_argument("--fusion-lifecycle", type=Path)
    Parser.add_argument("--native-ready", action="store_true")
    Parser.add_argument("--prepare-only", action="store_true")
    Parser.add_argument("--watch", action="store_true")
    Parser.add_argument(
        "--step",
        action="store_true",
        help="Run one step with freshly loaded recipe bindings",
    )
    Parser.add_argument(
        "--authoring-grid", choices=("baseline", "three-values"), default="three-values"
    )
    Parser.add_argument("--recipe-seconds", type=int, default=1200)
    Parser.add_argument("--max-seconds", type=int, default=3600)
    Parser.add_argument("--max-recipes", type=int, default=10000)
    AddBuilderOptions(Parser)
    Args = Parser.parse_args()
    CheckBuilderOptions(Parser, Args)
    if not (Args.solidworks_catalogue or Args.fusion_catalogue) and not (
        Args.auto_develop_builders and (Args.builder_resume or Args.builder_pause)
    ):
        Parser.error("select at least one application catalogue")
    if min(Args.recipe_seconds, Args.max_seconds, Args.max_recipes) < 1:
        Parser.error("time and recipe limits must be positive")
    for Name in (
        "directory",
        "solidworks_catalogue",
        "fusion_catalogue",
        "solidworks_host",
        "native_config",
        "fusion_lifecycle",
        "builder_api_metadata",
        "builder_registry",
    ):
        Value = getattr(Args, Name)
        if Value is not None:
            setattr(Args, Name, Value.resolve())
    return Args


# preparation includes written recipes without builders instead of silently omitting most features
def CampaignStep(Args):
    SourceRoot = Path(__file__).resolve().parents[3]
    if Args.directory.is_relative_to(SourceRoot):
        raise ValueError("use a campaign directory outside the source checkout")
    Catalogues = {}
    if Args.solidworks_catalogue:
        Catalogues["solidworks"] = ReadCatalogue(
            Args.solidworks_catalogue.resolve(), None
        )
    if Args.fusion_catalogue:
        Catalogues["fusion"] = ReadFusionCatalogue(
            Args.fusion_catalogue.resolve(), None
        )
    PlanValue = PlanRecipes(SourceRoot, Catalogues)
    if Args.directory.exists() and not (Args.directory / "Campaign.json").exists():
        raise ValueError("existing campaign directory has no campaign record")
    Args.directory.mkdir(mode=0o700, exist_ok=True)
    with HoldCatalogue(Args.directory):
        State = MergePlan(Args.directory, PlanValue)
        ReadReply(Args.directory, State)
        Ready = [
            Entry
            for Entry in State["entries"].values()
            if Entry["status"] in {"pending", "running"}
        ]
        if Ready and not Args.prepare_only:
            Entry = min(
                Ready, key=lambda Value: (Value["application"], Value["recipe_id"])
            )
            ApplyRecipe(Args, Entry, SourceRoot, State)
        Packet = WriteNext(Args.directory, State, SourceRoot)
        Summary = Summarize(State)
        Summary["next_recipe"] = (
            None if Packet is None else str(Args.directory / "NextRecipe.json")
        )
        WriteState(Args.directory / "Campaign.json", State)
        WriteState(Args.directory / "CampaignResult.json", Summary)
        print(dumps(Summary, sort_keys=True), flush=True)
        if Args.prepare_only:
            return 0
        if any(Entry["status"] == "pending" for Entry in State["entries"].values()):
            return 0
        return (
            3
            if Packet is not None
            else (
                2
                if Summary["features_without_written_recipe"]
                or any(
                    Entry["status"] != "verified_reader_report"
                    for Entry in State["entries"].values()
                )
                else 0
            )
        )


# fresh step processes observe assistant code changes without reusing imported stale builders
def MainCampaign():
    Args = ReadOptions()
    if Args.auto_develop_builders:
        from InferenceGrid.BuilderDevelopment.RunDevelopment import RunDevelopment

        Result = RunDevelopment(Args, Path(__file__).resolve().parents[3])
        print(dumps(Result, sort_keys=True), flush=True)
        return (
            0
            if Result["status"]
            in {"completed", "prepared", "paused", "pause_requested"}
            else 3
        )
    if Args.prepare_only or Args.step:
        return CampaignStep(Args)
    Command = [
        executable,
        str(Path(__file__).resolve()),
        *[Arg for Arg in argv[1:] if Arg != "--watch"],
        "--step",
    ]
    Deadline = monotonic() + Args.max_seconds
    for _ in range(Args.max_recipes):
        Seconds = max(1, min(Args.recipe_seconds, int(Deadline - monotonic())))
        Result = run([*Command, "--recipe-seconds", str(Seconds)], check=False)
        if Result.returncode not in {0, 2, 3}:
            return Result.returncode
        if Result.returncode == 2 or (Result.returncode == 3 and not Args.watch):
            return Result.returncode
        SummaryPath = Args.directory / "CampaignResult.json"
        Summary = loads(SummaryPath.read_text(encoding="utf-8"))
        if not Summary["statuses"].get("pending") and Result.returncode == 0:
            return 0
        if monotonic() >= Deadline:
            return 3
        if Result.returncode == 3:
            sleep(min(2, max(0, Deadline - monotonic())))
    return 3


# command failures leave accepted evidence untouched and return an explicit nonzero result
if __name__ == "__main__":
    try:
        raise SystemExit(MainCampaign())
    except (OSError, ValueError, KeyError, TypeError) as Error:
        raise SystemExit("recipe campaign refused: " + str(Error))
