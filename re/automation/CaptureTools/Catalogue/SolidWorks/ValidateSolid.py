# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite

from CaptureTools.Catalogue.Recipes.CompileRecipe import CompileRecipe

# the reviewed builders expose these driving quantities and no inferred controls
KDefaultParams = {
    "P01": {"width_mm": 40, "height_mm": 20},
    "P02": {"diameter_mm": 10},
    "P03": {"width_mm": 40, "height_mm": 20, "depth_mm": 10},
    "P04": {
        "width_mm": 40,
        "height_mm": 20,
        "depth_mm": 10,
        "cut_width_mm": 10,
        "cut_height_mm": 8,
        "cut_depth_mm": 4,
    },
    "P05": {
        "inner_radius_mm": 2,
        "outer_radius_mm": 6,
        "height_mm": 12,
        "angle_deg": 360,
    },
}


# unsupported controls must fail before a native process can be started
def ValidateSolid(CaseValue):
    if not isinstance(CaseValue, dict) or set(CaseValue) - {
        "recipe",
        "parameters",
        "options",
    }:
        raise ValueError("invalid SOLIDWORKS authoring case fields")
    RecipeKey = CaseValue.get("recipe")
    if not isinstance(RecipeKey, str) or RecipeKey not in KDefaultParams:
        return CompileRecipe(CaseValue)
    Overrides = CaseValue.get("parameters", {})
    if (
        not isinstance(Overrides, dict)
        or set(Overrides) - KDefaultParams[RecipeKey].keys()
    ):
        raise ValueError("unknown SOLIDWORKS driving parameter")
    Params = {**KDefaultParams[RecipeKey], **Overrides}
    if any(
        type(Value) not in (int, float) or not isfinite(Value) or Value <= 0
        for Value in Params.values()
    ):
        raise ValueError(
            "SOLIDWORKS driving parameters must be finite positive numbers"
        )
    Options = CaseValue.get("options", {})
    if not isinstance(Options, dict) or set(Options) - {
        "basis",
        "direction",
        "termination",
    }:
        raise ValueError("unknown SOLIDWORKS authoring option")
    Options = {
        "basis": "XZ" if RecipeKey == "P05" else "XY",
        "direction": 1,
        "termination": "blind",
        **Options,
    }
    if Options["basis"] not in ("XY", "YZ", "XZ"):
        raise ValueError("SOLIDWORKS basis must be XY YZ or XZ")
    if type(Options["direction"]) is not int or Options["direction"] not in (-1, 1):
        raise ValueError("SOLIDWORKS direction must be integer one or minus one")
    if Options["termination"] not in ("blind", "through_all"):
        raise ValueError("SOLIDWORKS termination must be blind or through_all")
    if RecipeKey != "P03" and Options["direction"] != 1:
        raise ValueError("only the P03 boss supports reversed authoring")
    if RecipeKey != "P04" and Options["termination"] != "blind":
        raise ValueError("only the P04 cut supports through_all authoring")
    if RecipeKey == "P05" and (
        Options["basis"] != "XZ"
        or Params["inner_radius_mm"] >= Params["outer_radius_mm"]
        or Params["angle_deg"] > 360
    ):
        raise ValueError("P05 requires XZ support ordered radii and angle at most 360")
    if RecipeKey == "P04" and (
        Params["cut_width_mm"] >= Params["width_mm"]
        or Params["cut_height_mm"] >= Params["height_mm"]
        or Params["cut_depth_mm"] >= Params["depth_mm"]
    ):
        raise ValueError("P04 requires a cut strictly inside the parent dimensions")
    return {"recipe": RecipeKey, "parameters": Params, "options": Options}
