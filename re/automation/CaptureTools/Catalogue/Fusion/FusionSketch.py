# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isclose

from CaptureTools.Catalogue.Fusion.FusionExpected import KFusionAxes


# closed sketch boundaries must retain the requested location rather than merely equal area
def CheckRectangle(Curves, Corners):
    Remaining = [(Corners[Index], Corners[(Index + 1) % 4]) for Index in range(4)]
    Lines = [
        Curve
        for Curve in Curves
        if not Curve["construction"] and not Curve["reference"]
    ]
    if len(Lines) != 4 or any(Curve["type"] != "SketchLine" for Curve in Lines):
        raise RuntimeError("fusion rectangle no longer has four ordinary lines")
    for Curve in Lines:
        Endpoints = (Curve["start_world_mm"], Curve["end_world_mm"])
        Matches = []
        for Index, Edge in enumerate(Remaining):
            for Ordered in (Edge, Edge[::-1]):
                if all(
                    isclose(Actual, Target, rel_tol=1e-9, abs_tol=1e-6)
                    for Actual, Target in zip(
                        (*Endpoints[0], *Endpoints[1]),
                        (*Ordered[0], *Ordered[1]),
                        strict=True,
                    )
                ):
                    Matches.append(Index)
                    break
        if len(Matches) != 1:
            raise RuntimeError(
                "fusion rectangle endpoints differ from the requested world geometry"
            )
        Remaining.pop(Matches[0])


# profile verification retains support placement and live source geometry across every rebuild
def CheckSketch(Sketches, Case):
    Recipe, Values, Options = Case["recipe"], Case["parameters"], Case["options"]
    if len(Sketches) != (2 if Recipe == "P04" else 1):
        raise RuntimeError("fusion sketch roster differs from the requested recipe")
    if any(Sketch["health"]["state"] != "healthy" for Sketch in Sketches):
        raise RuntimeError("fusion reported an unhealthy sketch")
    Required = (
        [{"diameter_mm"}]
        if Recipe == "P02"
        else (
            [{"inner_radius_mm", "outer_radius_mm", "height_mm"}]
            if Recipe == "P05"
            else [{"width_mm", "height_mm"}]
        )
    )
    if Recipe == "P04":
        Required.append(
            {"cut_width_mm", "cut_height_mm", "cut_center_u_mm", "cut_center_v_mm"}
        )
    for Sketch, Needed in zip(Sketches, Required, strict=True):
        Driving = {
            Dimension["parameter"]
            for Dimension in Sketch["dimensions"]
            if Dimension["driving"] is True
        }
        if not Needed <= Driving:
            raise RuntimeError("fusion lost a required driving sketch dimension")
        Constraints = [Constraint["type"] for Constraint in Sketch["constraints"]]
        if Recipe != "P04" or Sketch is Sketches[0]:
            if "CoincidentConstraint" not in Constraints:
                raise RuntimeError("fusion lost the profile origin or axis coincidence")
        if Recipe != "P02" and (
            Constraints.count("HorizontalConstraint") != 2
            or Constraints.count("VerticalConstraint") != 2
        ):
            raise RuntimeError("fusion lost a rectangle orientation constraint")
    if Recipe == "P02":
        Curves = Sketches[0]["curves"]
        if (
            len(Curves) != 1
            or Curves[0]["type"] != "SketchCircle"
            or not isclose(
                Curves[0]["radius_mm"],
                Values["diameter_mm"] / 2,
                rel_tol=1e-9,
                abs_tol=1e-6,
            )
            or any(abs(Value) > 1e-6 for Value in Curves[0]["center_world_mm"])
        ):
            raise RuntimeError(
                "fusion circle geometry differs from its driving diameter and origin"
            )
        return
    if Recipe == "P05":
        Corners = [
            (Values["inner_radius_mm"], 0, 0),
            (Values["outer_radius_mm"], 0, 0),
            (Values["outer_radius_mm"], 0, Values["height_mm"]),
            (Values["inner_radius_mm"], 0, Values["height_mm"]),
        ]
        CheckRectangle(Sketches[0]["curves"], Corners)
        return
    Axes = KFusionAxes[Options["basis"]]
    Width, Height = Values["width_mm"], Values["height_mm"]
    LocalPoints = [(0, 0, 0), (Width, 0, 0), (Width, Height, 0), (0, Height, 0)]
    Corners = [
        [
            sum(Point[Local] * Axes[Local][World] for Local in range(3))
            for World in range(3)
        ]
        for Point in LocalPoints
    ]
    CheckRectangle(Sketches[0]["curves"], Corners)
    if Recipe == "P04":
        CutWidth, CutHeight, Depth = (
            Values["cut_width_mm"],
            Values["cut_height_mm"],
            Values["depth_mm"],
        )
        LowerU, LowerV = (Width - CutWidth) / 2, (Height - CutHeight) / 2
        LocalPoints = [
            (LowerU, LowerV, Depth),
            (LowerU + CutWidth, LowerV, Depth),
            (LowerU + CutWidth, LowerV + CutHeight, Depth),
            (LowerU, LowerV + CutHeight, Depth),
        ]
        Corners = [
            [
                sum(Point[Local] * Axes[Local][World] for Local in range(3))
                for World in range(3)
            ]
            for Point in LocalPoints
        ]
        CheckRectangle(Sketches[1]["curves"], Corners)
