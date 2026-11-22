# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite

from CaptureTools.Catalogue.Recipes.RecipeRegistry import KRecipeBuilders


# compilation never interprets prose or accepts controls absent from the reviewed executable descriptor
def RecipeRules(CaseValue):
    if not isinstance(CaseValue, dict) or set(CaseValue) - {
        "recipe",
        "parameters",
        "options",
    }:
        raise ValueError("recipe case requires recipe parameters and options only")
    RecipeKey = CaseValue.get("recipe")
    if not isinstance(RecipeKey, str) or RecipeKey not in KRecipeBuilders:
        raise ValueError("recipe has no reviewed reusable executable builder")
    Descriptor = KRecipeBuilders[RecipeKey]
    Overrides = CaseValue.get("parameters", {})
    Options = CaseValue.get("options", {})
    if (
        not isinstance(Overrides, dict)
        or set(Overrides) - Descriptor["defaults"].keys()
    ):
        raise ValueError("unknown reusable recipe driving parameter")
    if not isinstance(Options, dict) or set(Options) - {
        "basis",
        "direction",
        "variant",
        "program",
    }:
        raise ValueError("unknown reusable recipe option")
    Parameters = {**Descriptor["defaults"], **Overrides}
    for ParamName, ParamValue in Parameters.items():
        Lower, Upper = Descriptor["domains"][ParamName]
        if (
            type(ParamValue) not in (int, float)
            or not isfinite(ParamValue)
            or not Lower <= ParamValue <= Upper
        ):
            raise ValueError(
                f"recipe parameter {ParamName} is outside its finite numeric domain"
            )
        Parameters[ParamName] = float(ParamValue)
    Basis = Options.get("basis", "XZ" if Descriptor["operation"] == "revolve" else "XY")
    Direction = Options.get("direction", 1)
    Variant = Options.get("variant", "baseline")
    if not isinstance(Basis, str) or Basis not in Descriptor["basis"]:
        raise ValueError("reusable recipe does not support the selected basis")
    if type(Direction) is not int or Direction not in Descriptor["direction"]:
        raise ValueError("reusable recipe does not support the selected direction")
    if (
        not isinstance(Variant, str)
        or Variant not in ("baseline", "units-inch", "midplane-wall")
        or (Variant == "midplane-wall" and RecipeKey != "extrude-thin")
    ):
        raise ValueError("reusable recipe does not implement the selected variant")
    if (
        "inner_radius_mm" in Parameters
        and Parameters["inner_radius_mm"] >= Parameters["outer_radius_mm"]
    ):
        raise ValueError("revolution radii must remain strictly ordered")
    if (
        "angle1_deg" in Parameters
        and Parameters["angle1_deg"] + Parameters["angle2_deg"] > 360
    ):
        raise ValueError(
            "two direction revolution angles must sum to at most 360 degrees"
        )
    return {
        "recipe": RecipeKey,
        "parameters": Parameters,
        "options": {"basis": Basis, "direction": Direction, "variant": Variant},
    }, Descriptor
