# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isclose, pi


# explicit basis transforms prevent world geometry from hiding incorrect support planes
def ProfileWorld(Basis, Point):
    First, Second, Third = Point
    return (
        [Third, First, Second]
        if Basis == "YZ"
        else [First, -Third, Second] if Basis == "XZ" else list(Point)
    )


# native coordinates need tolerant comparisons without accepting missing axes or coordinates
def IsSamePoint(Actual, Expected):
    return len(Actual) == len(Expected) == 3 and all(
        isclose(First, Second, rel_tol=1e-9, abs_tol=1e-6)
        for First, Second in zip(Actual, Expected, strict=True)
    )


# profile evidence must describe the authored editable sketch rather than an inferred prism
def CheckProfile(CaseValue, Observed):
    Program = CaseValue["options"]["program"]
    Profile = Program["profile"]
    Basis = CaseValue["options"]["basis"]
    Sketches = Observed["sketches"]
    if len(Sketches) != (2 if Program["seed"] is not None else 1) or any(
        Sketch["fully_defined"] is not True or Sketch["constraint_status"] != 3
        for Sketch in Sketches
    ):
        raise ValueError(
            "SOLIDWORKS written recipe lacks fully defined native sketches"
        )
    Sketch = next(Sketch for Sketch in Sketches if Sketch["name"] == "RecipeProfile")
    PlaneName = {"XY": "Front Plane", "YZ": "Right Plane", "XZ": "Top Plane"}[Basis]
    if Profile["support"] == "plane":
        if Sketch["support_type"] != 4 or Sketch["support_name"] != PlaneName:
            raise ValueError("SOLIDWORKS written recipe sketch plane differs")
    elif Sketch["support_type"] != 2:
        raise ValueError("SOLIDWORKS written recipe lost its parent face support")
    Entities = [
        Entity for Entity in Sketch["entities"] if Entity["construction"] is False
    ]
    Kind = Profile["kind"]
    Origin = Profile["origin_mm"]
    if Kind == "circle":
        Area = pi * Profile["diameter_mm"] ** 2 / 4
        if (
            len(Entities) != 1
            or not IsSamePoint(
                Entities[0]["center_world_mm"], ProfileWorld(Basis, Origin)
            )
            or not isclose(
                Entities[0]["radius_mm"],
                Profile["diameter_mm"] / 2,
                rel_tol=1e-9,
                abs_tol=1e-6,
            )
        ):
            raise ValueError("SOLIDWORKS native circle geometry differs")
    else:
        if Kind == "open_line":
            Finish = list(Origin)
            Finish[0 if Profile["axis"] == "u" else 1] += Profile["length_mm"]
            Edges = [(Origin, Finish)]
            Area = None
        else:
            Left = (
                Profile["inner_radius_mm"] if Kind == "radial_rectangle" else Origin[0]
            )
            Right = (
                Profile["outer_radius_mm"]
                if Kind == "radial_rectangle"
                else Left + Profile["width_mm"]
            )
            Bottom, Normal = Origin[1:]
            Top = Bottom + Profile["height_mm"]
            Corners = [
                [Left, Bottom, Normal],
                [Right, Bottom, Normal],
                [Right, Top, Normal],
                [Left, Top, Normal],
            ]
            Edges = list(zip(Corners, Corners[1:] + Corners[:1], strict=True))
            Area = (Right - Left) * Profile["height_mm"]
        if len(Entities) != len(Edges):
            raise ValueError("SOLIDWORKS native profile entity roster differs")
        Remaining = list(Entities)
        for First, Second in Edges:
            First, Second = ProfileWorld(Basis, First), ProfileWorld(Basis, Second)
            Matches = [
                Entity
                for Entity in Remaining
                if (
                    IsSamePoint(Entity["start_world_mm"], First)
                    and IsSamePoint(Entity["end_world_mm"], Second)
                )
                or (
                    IsSamePoint(Entity["end_world_mm"], First)
                    and IsSamePoint(Entity["start_world_mm"], Second)
                )
            ]
            if len(Matches) != 1:
                raise ValueError("SOLIDWORKS native profile edges differ")
            Remaining.remove(Matches[0])
    if Sketch["region_count"] != (0 if Area is None else 1) or (
        Area is not None
        and not isclose(Sketch["section_area_mm2"], Area, rel_tol=1e-9, abs_tol=1e-6)
    ):
        raise ValueError("SOLIDWORKS native profile region or area differs")
    Axes = [Entity for Entity in Sketch["entities"] if Entity["construction"] is True]
    if Program["operation"]["kind"] == "revolve" and (
        len(Axes) != 1
        or not IsSamePoint(Axes[0]["start_world_mm"], [0, 0, 0])
        or not IsSamePoint(Axes[0]["end_world_mm"], [0, 0, 30])
    ):
        raise ValueError("SOLIDWORKS revolution lost its world z construction axis")
