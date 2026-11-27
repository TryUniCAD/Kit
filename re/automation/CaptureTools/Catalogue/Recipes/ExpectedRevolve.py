# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import cos, pi, radians, sin


# annular sector moments distinguish symmetric and independent angular extents without vendor geometry
def ExpectedRevolve(Program):
    Profile, Operation = Program["profile"], Program["operation"]
    if Profile["kind"] == "open_line":
        Inner = Profile["radius_mm"]
        Outer = Inner + Operation["thin"]["thickness_mm"]
        Height = Profile["length_mm"]
    else:
        Inner, Outer, Height = (
            Profile["inner_radius_mm"],
            Profile["outer_radius_mm"],
            Profile["height_mm"],
        )
    First, Second = radians(Operation["angle1_deg"]), radians(Operation["angle2_deg"])
    if Operation["end"]["kind"] == "midplane":
        Lower, Upper = -First / 2, First / 2
    elif Operation["end"]["kind"] == "two_direction":
        Lower, Upper = -Second, First
    else:
        Lower, Upper = 0.0, First
    Span = Upper - Lower
    Volume = Span * (Outer**2 - Inner**2) * Height / 2
    Scale = 2 * (Outer**3 - Inner**3) / (3 * Span * (Outer**2 - Inner**2))
    Center = [
        Scale * (sin(Upper) - sin(Lower)),
        Scale * (cos(Lower) - cos(Upper)),
        Height / 2,
    ]
    Angles = [
        Lower,
        Upper,
        *(Index * pi / 2 for Index in range(-4, 9) if Lower <= Index * pi / 2 <= Upper),
    ]
    Points = [
        (Radius * cos(Angle), Radius * sin(Angle))
        for Angle in Angles
        for Radius in (Inner, Outer)
    ]
    Bounds = [
        [min(Point[0] for Point in Points), min(Point[1] for Point in Points), 0.0],
        [max(Point[0] for Point in Points), max(Point[1] for Point in Points), Height],
    ]
    if Operation["effect"] == "cut":
        Seed = Program["seed"]
        Radius = Seed["diameter_mm"] / 2
        SeedVolume = pi * Radius**2 * Seed["height_mm"]
        Remaining = SeedVolume - Volume
        Center = [
            -Volume * Center[0] / Remaining,
            -Volume * Center[1] / Remaining,
            (SeedVolume * Seed["height_mm"] / 2 - Volume * Center[2]) / Remaining,
        ]
        Volume = Remaining
        Bounds = [[-Radius, -Radius, 0.0], [Radius, Radius, Seed["height_mm"]]]
    return {
        "body_count": 1,
        "volume_mm3": Volume,
        "center_of_mass_mm": Center,
        "bounds_mm": Bounds,
    }
