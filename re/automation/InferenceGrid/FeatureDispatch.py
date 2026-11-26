# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
from pathlib import Path
import sqlite3
import subprocess
import sys

sys.path[:0] = [
    str(Path(__file__).resolve().parents[1]),
    str(Path(__file__).resolve().parents[3] / "src"),
]

from Corpus import git
from InferenceGrid.FeatureCatalogue import ReadCatalogue
from InferenceGrid.FeatureFusionCatalogue import ReadFusionCatalogue
from InferenceGrid.FeatureRoutes import FeatureRecipes
from InferenceGrid.FeatureSpecs import DescribeSpec
from Records import bounded, canonical, label

# executable recipe provenance is tied to the current checkout
SourceRoot = Path(__file__).resolve().parents[3]


# one set of arguments supports catalogue planning and the existing worker commands
def DispatchParser():
    parser = argparse.ArgumentParser(
        description="Plan and dispatch SOLIDWORKS and Fusion catalogue features deterministically"
    )
    parser.add_argument("--store", type=Path)
    parser.add_argument("--feature")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--catalogue", type=Path)
    source.add_argument("--fusion-catalogue", type=Path)
    parser.add_argument("--catalogue-sha256")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("manifest")
    commands.add_parser("plan")
    commands.add_parser("recipe")
    commands.add_parser("submit")
    commands.add_parser("status")
    advance = commands.add_parser("advance")
    advance.add_argument("--config", type=Path, required=True)
    advance.add_argument("--kind", required=True)
    advance.add_argument("--resource", required=True)
    advance.add_argument("--wait-seconds", type=int, default=0)
    return parser


# catalogue planning never touches the controller or creates jobs for blocked entries
def DispatchFeature(parser, args):
    catalogue = LoadCatalogue(parser, args)
    if args.command == "manifest":
        if catalogue is None or args.feature is not None:
            parser.error("manifest requires a catalogue and takes no --feature")
        return catalogue
    if args.feature is None:
        parser.error(f"{args.command} requires --feature")
    if args.command == "recipe":
        written = DescribeSpec(args.feature)
        if written is None:
            parser.error(f"{args.feature!r} has no written recipe")
        return written
    recipe = FeatureRecipes.get(args.feature)
    plan = None if catalogue is None else catalogue["features"].get(args.feature)
    if (catalogue is not None and plan is None) or (
        catalogue is None and recipe is None
    ):
        parser.error(f"invalid choice: {args.feature!r} is not a known feature ID")
    if args.command == "plan" or recipe is None:
        if plan is None:
            parser.error("plan requires a catalogue")
        return {**plan, "catalogue_sha256": catalogue["catalogue_sha256"]}
    if args.store is None:
        parser.error(f"{args.command} requires --store for a mapped feature")
    return {"feature": args.feature, **RunRecipe(recipe, args)}


# an explicit source selector keeps the two independent catalogue schemas distinct
def LoadCatalogue(parser, args):
    if args.catalogue is not None:
        return ReadCatalogue(args.catalogue, args.catalogue_sha256)
    if args.fusion_catalogue is not None:
        return ReadFusionCatalogue(args.fusion_catalogue, args.catalogue_sha256)
    if args.catalogue_sha256:
        parser.error("--catalogue-sha256 requires a catalogue")
    return None


# commands share one reviewed route while native advancement remains explicitly scoped
def RunRecipe(recipe, args):
    if args.command == "submit":
        revision = git(SourceRoot, "rev-parse", "HEAD").decode("ascii").strip()
        return recipe.Submit(args.store, revision)
    if args.command == "advance":
        if recipe.Advance is None:
            return {"scope": recipe.Scope, "status": "no_evidence_experiment"}
        return recipe.Advance(
            args.store,
            args.config,
            label(args.kind),
            label(args.resource),
            bounded(args.wait_seconds, 0, 3600),
        )
    return recipe.Status(args.store)


# the public process uses stable JSON output for automation callers
def MainDispatch():
    parser = DispatchParser()
    args = parser.parse_args()
    try:
        output = canonical(DispatchFeature(parser, args))
        sys.stdout.buffer.write((output + "\n").encode("utf-8"))
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        RuntimeError,
        RecursionError,
        sqlite3.Error,
        subprocess.SubprocessError,
    ) as error:
        parser.exit(1, f"catalogue feature dispatch refused: {error}\n")


if __name__ == "__main__":
    MainDispatch()
