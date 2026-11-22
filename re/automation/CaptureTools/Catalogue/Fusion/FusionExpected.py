# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import cos, pi, radians, sin

from CaptureTools.Catalogue.Fusion.FusionParams import ValidateFusion

# source plane names must not substitute for explicit world coordinate transforms
KFusionAxes = {
    "XY": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    "YZ": ((0, 1, 0), (0, 0, 1), (1, 0, 0)),
    "XZ": ((1, 0, 0), (0, 0, 1), (0, -1, 0)),
}


# independent analytic expectations expose wrong direction termination and parameter application
def ExpectFusion(Case):
    Normal = ValidateFusion(Case)
    Recipe, Values, Options = Normal["recipe"], Normal["parameters"], Normal["options"]
    if Recipe in ("P01", "P02"):
        Area = (
            Values["width_mm"] * Values["height_mm"]
            if Recipe == "P01"
            else pi * Values["diameter_mm"] ** 2 / 4
        )
        return {
            "body_count": 0,
            "area_mm2": Area,
            "volume_mm3": None,
            "center_of_mass_mm": None,
        }
    if Recipe == "P05":
        Inner, Outer = Values["inner_radius_mm"], Values["outer_radius_mm"]
        Angle = radians(Values["angle_deg"])
        Scale = 2 * (Outer**3 - Inner**3) / (3 * Angle * (Outer**2 - Inner**2))
        return {
            "body_count": 1,
            "volume_mm3": Angle * (Outer**2 - Inner**2) * Values["height_mm"] / 2,
            "center_of_mass_mm": [
                Scale * sin(Angle),
                Scale * (1 - cos(Angle)),
                Values["height_mm"] / 2,
            ],
        }
    Width, Height, Depth = Values["width_mm"], Values["height_mm"], Values["depth_mm"]
    Volume = Width * Height * Depth
    Center = [Width / 2, Height / 2, Options["direction"] * Depth / 2]
    if Recipe == "P04":
        CutDepth = (
            Depth if Options["termination"] == "through_all" else Values["cut_depth_mm"]
        )
        Removed = Values["cut_width_mm"] * Values["cut_height_mm"] * CutDepth
        Center[2] = (Volume * Depth / 2 - Removed * (Depth - CutDepth / 2)) / (
            Volume - Removed
        )
        Volume -= Removed
    Axes = KFusionAxes[Options["basis"]]
    return {
        "body_count": 1,
        "volume_mm3": Volume,
        "center_of_mass_mm": [
            sum(Center[Local] * Axes[Local][World] for Local in range(3))
            for World in range(3)
        ],
    }
