# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import cos, isclose, pi, radians, sin


# source measurements must match the requested geometry rather than merely contain a body
def CheckSolidShape(CaseValue, Observed):
    RecipeKey = CaseValue["recipe"]
    Params = CaseValue["parameters"]
    Options = CaseValue["options"]
    Sketches = Observed["sketches"]
    if not Sketches or any(Sketch["fully_defined"] is not True for Sketch in Sketches):
        raise ValueError("SOLIDWORKS authored sketches are not fully defined")
    PlaneName = {"XY": "Front Plane", "YZ": "Right Plane", "XZ": "Top Plane"}[
        Options["basis"]
    ]
    if Sketches[0]["support_name"] != PlaneName or Sketches[0]["support_type"] != 4:
        raise ValueError(
            "SOLIDWORKS authored sketch support differs from the configured basis"
        )
    if RecipeKey == "P04" and (len(Sketches) != 2 or Sketches[1]["support_type"] != 2):
        raise ValueError("SOLIDWORKS configured cut lost its native face support")
    if any(
        Feature["suppressed"] or Feature["error_code"] != 0 or Feature["warning"]
        for Feature in Observed["feature_tree"]
    ):
        raise ValueError("SOLIDWORKS authored feature tree is not healthy")
    Dimensions = {}
    for Feature in Observed["feature_tree"]:
        for Dimension in Feature["dimensions"]:
            Dimensions.setdefault(Dimension["name"], []).append(
                Dimension["system_value"]
            )
    for ParamName, ParamValue in Params.items():
        if ParamName == "cut_depth_mm" and Options["termination"] == "through_all":
            continue
        Expected = (
            radians(ParamValue) if ParamName == "angle_deg" else ParamValue / 1000
        )
        Values = Dimensions.get(ParamName, [])
        if not Values or any(
            not isclose(Value, Expected, rel_tol=1e-9, abs_tol=1e-9) for Value in Values
        ):
            raise ValueError(
                "SOLIDWORKS requested driving parameter differs from native measurement "
                + ParamName
            )
    if RecipeKey in ("P01", "P02"):
        AreaValue = (
            Params["width_mm"] * Params["height_mm"]
            if RecipeKey == "P01"
            else pi * Params["diameter_mm"] ** 2 / 4
        )
        if Observed["body_count"] != 0 or not isclose(
            Sketches[0]["section_area_mm2"], AreaValue, rel_tol=1e-9, abs_tol=1e-6
        ):
            raise ValueError(
                "SOLIDWORKS sketch area or body count differs from the configured case"
            )
        return
    if RecipeKey == "P05":
        Inner = Params["inner_radius_mm"]
        Outer = Params["outer_radius_mm"]
        Height = Params["height_mm"]
        Angle = radians(Params["angle_deg"])
        Volume = Angle * (Outer**2 - Inner**2) * Height / 2
        Factor = 2 * (Outer**3 - Inner**3) / (3 * Angle * (Outer**2 - Inner**2))
        Center = [Factor * sin(Angle), Factor * (1 - cos(Angle)), Height / 2]
    else:
        Width, Height, Depth = (
            Params[Name] for Name in ("width_mm", "height_mm", "depth_mm")
        )
        Volume = Width * Height * Depth
        LocalZ = Depth / 2
        if RecipeKey == "P04":
            CutDepth = (
                Depth
                if Options["termination"] == "through_all"
                else Params["cut_depth_mm"]
            )
            Removed = Params["cut_width_mm"] * Params["cut_height_mm"] * CutDepth
            LocalZ = (Volume * Depth / 2 - Removed * (Depth - CutDepth / 2)) / (
                Volume - Removed
            )
            Volume -= Removed
        LocalZ *= Options["direction"]
        Basis = Options["basis"]
        Center = (
            [LocalZ, Width / 2, Height / 2]
            if Basis == "YZ"
            else (
                [Width / 2, -LocalZ, Height / 2]
                if Basis == "XZ"
                else [Width / 2, Height / 2, LocalZ]
            )
        )
    if (
        Observed["body_count"] != 1
        or not isclose(Observed["volume_mm3"], Volume, rel_tol=1e-9, abs_tol=1e-6)
        or len(Observed["center_of_mass_mm"]) != 3
        or any(
            not isclose(Actual, Expected, rel_tol=1e-9, abs_tol=1e-6)
            for Actual, Expected in zip(
                Observed["center_of_mass_mm"], Center, strict=True
            )
        )
    ):
        raise ValueError(
            "SOLIDWORKS configured body volume or center of mass differs from native measurements"
        )
