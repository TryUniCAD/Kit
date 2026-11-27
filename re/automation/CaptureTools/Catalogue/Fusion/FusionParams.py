# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite

from CaptureTools.Catalogue.Fusion.FusionCases import KFusionDefaults


# invalid native requests must fail before application or document ownership changes
def ValidateFusion(Case):
    if not isinstance(Case, dict) or set(Case) - {"recipe", "parameters", "options"}:
        raise ValueError(
            "a fusion case requires recipe and optional parameters and options"
        )
    Recipe = Case.get("recipe")
    if not isinstance(Recipe, str) or Recipe not in KFusionDefaults:
        raise ValueError("fusion authoring supports only explicit P01 to P05 recipes")
    Supplied = Case.get("parameters", {})
    Options = Case.get("options", {})
    if not isinstance(Supplied, dict) or set(Supplied) - KFusionDefaults[Recipe].keys():
        raise ValueError("fusion case contains an unknown driving parameter")
    if not isinstance(Options, dict) or set(Options) - {
        "basis",
        "direction",
        "termination",
    }:
        raise ValueError("fusion case contains an unknown authoring option")
    Basis = Options.get("basis", "XZ" if Recipe == "P05" else "XY")
    Direction = Options.get("direction", 1)
    Termination = Options.get("termination", "blind")
    if Basis not in ("XY", "YZ", "XZ") or (Recipe == "P05" and Basis != "XZ"):
        raise ValueError("fusion case selects an unsupported sketch basis")
    if type(Direction) is not int or Direction not in (-1, 1):
        raise ValueError("fusion direction must be positive one or negative one")
    if Recipe != "P03" and Direction != 1:
        raise ValueError("only the blind boss recipe supports reversed direction")
    if Termination not in ("blind", "through_all") or (
        Recipe != "P04" and Termination != "blind"
    ):
        raise ValueError("only the cut recipe supports through all termination")
    Parameters = {**KFusionDefaults[Recipe], **Supplied}
    if Termination == "through_all":
        if "cut_depth_mm" in Supplied:
            raise ValueError("through all has no driving cut depth parameter")
        del Parameters["cut_depth_mm"]
    for ParamName, ParamValue in Parameters.items():
        if (
            type(ParamValue) not in (int, float)
            or not isfinite(ParamValue)
            or not 0.0001 <= ParamValue <= 100000
        ):
            raise ValueError(
                f"fusion parameter {ParamName} must be finite between 0.0001 and 100000"
            )
        Parameters[ParamName] = float(ParamValue)
    if Recipe == "P04":
        if (
            Parameters["cut_width_mm"] >= Parameters["width_mm"]
            or Parameters["cut_height_mm"] >= Parameters["height_mm"]
        ):
            raise ValueError(
                "the centered cut must remain strictly inside its parent profile"
            )
        if (
            Termination == "blind"
            and Parameters["cut_depth_mm"] >= Parameters["depth_mm"]
        ):
            raise ValueError(
                "the blind pocket depth must remain below its parent depth"
            )
    if Recipe == "P05" and (
        Parameters["inner_radius_mm"] >= Parameters["outer_radius_mm"]
        or Parameters["angle_deg"] > 360
    ):
        raise ValueError(
            "the revolution requires ordered radii and an angle at most 360 degrees"
        )
    return {
        "recipe": Recipe,
        "parameters": Parameters,
        "options": {"basis": Basis, "direction": Direction, "termination": Termination},
    }
