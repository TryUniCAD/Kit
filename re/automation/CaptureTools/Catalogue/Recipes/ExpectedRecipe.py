# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from itertools import product

from CaptureTools.Catalogue.Recipes.CompileRecipe import CompileRecipe
from CaptureTools.Catalogue.Recipes.ExpectedExtrude import ExpectedExtrude
from CaptureTools.Catalogue.Recipes.ExpectedRevolve import ExpectedRevolve

# an explicit right handed basis separates source sketch coordinates from vendor plane names
KRecipeAxes = {
    "XY": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    "YZ": ((0, 1, 0), (0, 0, 1), (1, 0, 0)),
    "XZ": ((1, 0, 0), (0, 0, 1), (0, -1, 0)),
}


# independent physical predictions never turn a successful native call into an acceptance claim
def ExpectedRecipe(CaseValue):
    Normal = CompileRecipe(CaseValue)
    Options = Normal["options"]
    Program = Options["program"]
    Operation = Program["operation"]
    if Operation["kind"] == "revolve":
        Expected = ExpectedRevolve(Program)
    else:
        Expected = ExpectedExtrude(Program, Options["direction"])
        Axes = KRecipeAxes[Options["basis"]]
        Center = Expected["center_of_mass_mm"]
        Expected["center_of_mass_mm"] = [
            sum(Center[Local] * Axes[Local][World] for Local in range(3))
            for World in range(3)
        ]
        Corners = product(*zip(*Expected["bounds_mm"], strict=True))
        Points = [
            [
                sum(Point[Local] * Axes[Local][World] for Local in range(3))
                for World in range(3)
            ]
            for Point in Corners
        ]
        Expected["bounds_mm"] = [
            [min(Point[Axis] for Point in Points) for Axis in range(3)],
            [max(Point[Axis] for Point in Points) for Axis in range(3)],
        ]
    Expected["semantic"] = {
        "profile_kind": Program["profile"]["kind"],
        "profile_support": Program["profile"]["support"],
        "operation_kind": Operation["kind"],
        "effect": Operation["effect"],
        "extent_kind": Operation["end"]["kind"],
        "basis": Options["basis"],
        "direction": Options["direction"],
        "start_offset_mm": (
            -Operation["start"]["offset_mm"]
            if Operation["start"]["reverse"]
            else Operation["start"]["offset_mm"]
        ),
        "thin_side": None if Operation["thin"] is None else Operation["thin"]["side"],
        "end_reference": (
            "EndPlane" if Operation["end"]["kind"] == "up_to_plane" else None
        ),
        "angles_deg": [Operation["angle1_deg"], Operation["angle2_deg"]],
    }
    return Expected
