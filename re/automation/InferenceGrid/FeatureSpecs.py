# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import ast
from functools import cache
import json
import math
from pathlib import Path
import sqlite3
import sys

sys.path[:0] = [
    str(Path(__file__).resolve().parents[1]),
    str(Path(__file__).resolve().parents[3] / "src"),
]

from Records import canonical, label

# written recipes live beside the paired specifications they extend
SpecPath = Path(__file__).resolve().parents[1] / "FeatureRecipeSpecs.json"

# paired recipes remain the single source for the reviewed P01 to P05 cases
PairPath = Path(__file__).resolve().parents[1] / "PairSpecs.json"

# the specification file fits inside an explicit read boundary
SpecBytes = 4 * 1024 * 1024

# each application keeps its own catalogue identity space
Applications = ("solidworks", "fusion")

# a volume change states how the feature relates to its seed body
Effects = {"adds", "removes", "keeps", "none"}

# formulas use only these named constants and single-argument functions
FormulaNames = {"pi": math.pi}

# trigonometric and root functions cover the analytic expectations in the recipes
FormulaCalls = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "radians": math.radians,
}

# arithmetic is limited to the operators a closed-form volume needs
FormulaOperators = {
    ast.Add: lambda Left, Right: Left + Right,
    ast.Sub: lambda Left, Right: Left - Right,
    ast.Mult: lambda Left, Right: Left * Right,
    ast.Div: lambda Left, Right: Left / Right,
    ast.Pow: lambda Left, Right: Left**Right,
}


# a bounded interpreter evaluates recorded formulas without executing text as code
def EvaluateFormula(Text):
    if not isinstance(Text, str) or not 0 < len(Text) <= 256:
        raise ValueError("recipe formula must be a short string")
    Value = FormulaNode(ast.parse(Text, mode="eval").body)
    if not math.isfinite(Value) or Value < 0:
        raise ValueError(f"recipe formula is not a finite non-negative value: {Text}")
    return Value


# each node kind is checked so that names, attributes and calls cannot escape
def FormulaNode(Node):
    if isinstance(Node, ast.Constant) and type(Node.value) in (int, float):
        return float(Node.value)
    if isinstance(Node, ast.Name) and Node.id in FormulaNames:
        return FormulaNames[Node.id]
    if isinstance(Node, ast.BinOp) and type(Node.op) in FormulaOperators:
        return FormulaOperators[type(Node.op)](
            FormulaNode(Node.left), FormulaNode(Node.right)
        )
    if isinstance(Node, ast.UnaryOp) and isinstance(Node.op, ast.USub):
        return -FormulaNode(Node.operand)
    if (
        isinstance(Node, ast.Call)
        and isinstance(Node.func, ast.Name)
        and Node.func.id in FormulaCalls
        and len(Node.args) == 1
        and not Node.keywords
    ):
        return FormulaCalls[Node.func.id](FormulaNode(Node.args[0]))
    raise ValueError("recipe formula uses an unsupported expression")


# optional volume formulas stay explicit as null when the result is not closed form
def OptionalVolume(Value):
    return None if Value is None else EvaluateFormula(Value)


# plain-language steps must be non-empty text so a person can author the case
def Steps(Value, Name):
    if (
        not isinstance(Value, list)
        or not Value
        or any(not isinstance(Step, str) or not Step.strip() for Step in Value)
    ):
        raise ValueError(f"{Name} must be a non-empty list of text steps")
    return Value


# a duplicate JSON field would make the recorded recipe ambiguous
def UniqueFields(Pairs):
    Values = dict(Pairs)
    if len(Values) != len(Pairs):
        raise ValueError("recipe specifications contain a duplicate field")
    return Values


# shared seeds give every recipe the same measured starting body
def ReadSeeds(Root):
    Seeds = {}
    for Name, Seed in Root["seeds"].items():
        Steps(Seed["build"], f"seed {Name} build")
        if type(Seed["bodies"]) is not int or Seed["bodies"] < 0:
            raise ValueError(f"seed {Name} has an invalid body count")
        Seeds[label(Name)] = {
            **Seed,
            "volume_value_mm3": OptionalVolume(Seed["volume_mm3"]),
        }
    return Seeds


# a recipe either reuses a paired recipe or states its complete authoring intent
def ReadRecipe(Recipe, Seeds, Pairs):
    Identity = label(Recipe["id"])
    if not isinstance(Recipe["name"], str) or not Recipe["name"].strip():
        raise ValueError(f"recipe {Identity} needs a name")
    if "pair_recipe" in Recipe:
        if Recipe["pair_recipe"] not in Pairs or set(Recipe) != {
            "id",
            "name",
            "entries",
            "pair_recipe",
        }:
            raise ValueError(f"recipe {Identity} must only reference a paired recipe")
        return {**Recipe, "kind": "paired"}
    Seed = Recipe["seed"]
    if Seed != "none" and Seed not in Seeds:
        raise ValueError(f"recipe {Identity} refers to an unknown seed")
    Steps(Recipe["build"], f"recipe {Identity} build")
    Parameters = Recipe["parameters"]
    if not isinstance(Parameters, dict) or any(
        type(Value) not in (int, float) for Value in Parameters.values()
    ):
        raise ValueError(f"recipe {Identity} parameters must be numbers")
    if not isinstance(Recipe["variations"], list) or any(
        not isinstance(Item, str) or not Item.strip() for Item in Recipe["variations"]
    ):
        raise ValueError(f"recipe {Identity} variations must be text")
    Expected = ReadExpectation(Identity, Recipe["expect"], Seeds.get(Seed))
    Edit = ReadEdit(Identity, Recipe.get("edit"), Parameters)
    return {**Recipe, "kind": "written", "expect": Expected, "edit": Edit}


# the stated volume must agree with whether the feature adds or removes material
def ReadExpectation(Identity, Expected, Seed):
    if type(Expected["bodies"]) is not int or Expected["bodies"] < 0:
        raise ValueError(f"recipe {Identity} has an invalid body count")
    if Expected["effect"] not in Effects:
        raise ValueError(f"recipe {Identity} has an unknown volume effect")
    if not isinstance(Expected["check"], str) or not Expected["check"].strip():
        raise ValueError(f"recipe {Identity} must state what to measure")
    Value = OptionalVolume(Expected["volume_mm3"])
    Base = None if Seed is None else Seed["volume_value_mm3"]
    if Value is not None and Base is not None:
        Relation = {
            "adds": Value > Base,
            "removes": Value < Base,
            "keeps": math.isclose(Value, Base, rel_tol=1e-9),
            "none": True,
        }[Expected["effect"]]
        if not Relation:
            raise ValueError(
                f"recipe {Identity} volume disagrees with its {Expected['effect']} effect"
            )
    return {**Expected, "volume_value_mm3": Value}


# a driving edit must change one recorded parameter to a different value
def ReadEdit(Identity, Edit, Parameters):
    if Edit is None:
        return None
    if Edit["parameter"] not in Parameters or type(Edit["value"]) not in (int, float):
        raise ValueError(f"recipe {Identity} edits an unknown parameter")
    if Edit["value"] == Parameters[Edit["parameter"]]:
        raise ValueError(f"recipe {Identity} edit does not change its parameter")
    return {**Edit, "volume_value_mm3": OptionalVolume(Edit["volume_mm3"])}


# every catalogue entry belongs to at most one recipe so plans cannot disagree
def ReadEntries(Recipe, Index):
    Entries = Recipe["entries"]
    if not isinstance(Entries, dict) or not set(Entries) <= set(Applications):
        raise ValueError(f"recipe {Recipe['id']} has invalid application entries")
    Count = 0
    for Application, Keys in Entries.items():
        if not isinstance(Keys, list):
            raise ValueError(f"recipe {Recipe['id']} entries must be arrays")
        for Key in Keys:
            if label(Key) in Index:
                raise ValueError(f"catalogue entry {Key} has more than one recipe")
            Index[Key] = Recipe["id"]
            Count += 1
    if not Count:
        raise ValueError(f"recipe {Recipe['id']} covers no catalogue entry")


# reviewed executable routes must point at the same paired recipe as their written entry
def CheckRoutes(Recipes, Index):
    from InferenceGrid.FeatureRoutes import FeatureRecipes

    for Key, Route in FeatureRecipes.items():
        Identity = Index.get(Key)
        if Identity is None:
            continue
        if Recipes[Identity].get("pair_recipe") != Route.Recipe:
            raise ValueError(f"recipe for {Key} differs from its reviewed route")


# the paired specification identities are read once from their own file
def PairIdentities():
    Root = json.loads(PairPath.read_bytes())
    return {label(Recipe["id"]) for Recipe in Root["recipes"]}


# the specification is validated as a whole before any plan uses one recipe
@cache
def ReadSpecs():
    Raw = SpecPath.read_bytes()
    if not 0 < len(Raw) <= SpecBytes:
        raise ValueError("recipe specifications exceed the supported byte limit")
    Root = json.loads(Raw, object_pairs_hook=UniqueFields)
    if not isinstance(Root, dict) or Root.get("schema_version") != 1:
        raise ValueError("unsupported recipe specification schema")
    Seeds = ReadSeeds(Root)
    Pairs = PairIdentities()
    Recipes, Index = {}, {}
    for Recipe in Root["recipes"]:
        Value = ReadRecipe(Recipe, Seeds, Pairs)
        if Value["id"] in Recipes:
            raise ValueError(f"recipe {Value['id']} is repeated")
        ReadEntries(Value, Index)
        Recipes[Value["id"]] = Value
    CheckRoutes(Recipes, Index)
    return {"root": Root, "seeds": Seeds, "recipes": Recipes, "index": Index}


# catalogue planners ask for the recipe identity of one entry
def SpecFor(Key):
    Specs = ReadSpecs()
    Identity = Specs["index"].get(Key)
    return None if Identity is None else Specs["recipes"][Identity]


# the readable form expands the seed so one entry can be authored on its own
def DescribeSpec(Key):
    Specs = ReadSpecs()
    Recipe = SpecFor(Key)
    if Recipe is None:
        return None
    Seed = Specs["seeds"].get(Recipe.get("seed"))
    return {
        "feature": Key,
        "recipe": Recipe,
        "seed": Seed,
        "status": Specs["root"]["status"],
        "conventions": Specs["root"]["conventions"],
    }


# scope coverage compares in-scope catalogue entries with the written recipes
def Coverage(Catalogue, Application):
    Specs = ReadSpecs()
    Scope = Specs["root"]["scope"][Application]
    Written = {
        Key for Key, Identity in Specs["index"].items()
        if Application in Specs["recipes"][Identity]["entries"]
        and Key in Specs["recipes"][Identity]["entries"][Application]
    }
    Unknown = sorted(Written - Catalogue.keys())
    if Application == "solidworks":
        Families = set(Scope["families"])
        InScope = {
            Key for Key, Plan in Catalogue.items() if Plan["family"] in Families
        }
    else:
        InScope = set(Catalogue) - set(Scope["excluded"])
    return {
        "in_scope": len(InScope),
        "written": len(InScope & Written),
        "missing": sorted(InScope - Written),
        "unknown": Unknown,
    }


# the check command validates the file and optionally measures catalogue coverage
def MainCheck():
    Parser = argparse.ArgumentParser(
        description="Validate written feature recipes and report their catalogue coverage"
    )
    Parser.add_argument("--solidworks-catalogue", type=Path)
    Parser.add_argument("--fusion-catalogue", type=Path)
    Args = Parser.parse_args()
    try:
        Specs = ReadSpecs()
        Report = {
            "recipes": len(Specs["recipes"]),
            "entries": len(Specs["index"]),
            "coverage": {},
        }
        if Args.solidworks_catalogue is not None:
            from InferenceGrid.FeatureCatalogue import ReadCatalogue

            Catalogue = ReadCatalogue(Args.solidworks_catalogue, None)["features"]
            Report["coverage"]["solidworks"] = Coverage(Catalogue, "solidworks")
        if Args.fusion_catalogue is not None:
            from InferenceGrid.FeatureFusionCatalogue import ReadFusionCatalogue

            Catalogue = ReadFusionCatalogue(Args.fusion_catalogue, None)["features"]
            Report["coverage"]["fusion"] = Coverage(Catalogue, "fusion")
    except (OSError, ValueError, TypeError, KeyError, sqlite3.Error) as Error:
        Parser.exit(1, f"recipe specification refused: {Error}\n")
    sys.stdout.buffer.write((canonical(Report) + "\n").encode("utf-8"))
    Rows = Report["coverage"].values()
    if any(Row["unknown"] for Row in Rows):
        return 1
    return 2 if any(Row["missing"] for Row in Rows) else 0


if __name__ == "__main__":
    raise SystemExit(MainCheck())
