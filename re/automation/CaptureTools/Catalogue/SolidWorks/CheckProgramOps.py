# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isclose, radians

from CaptureTools.Catalogue.SolidWorks.CheckProfile import ProfileWorld


# operation identity must survive native saving rather than merely produce equivalent geometry
def CheckProgramOps(CaseValue, Observed):
    Program = CaseValue["options"]["program"]
    Operation = Program["operation"]
    Feature = next(
        Feature
        for Feature in Observed["feature_tree"]
        if Feature["name"] == "RecipeFeature"
    )
    Reading = Feature["operation"]
    if (
        not isinstance(Reading, dict)
        or Reading["kind"] != Operation["kind"]
        or "RecipeProfile" not in Feature["parents"]
    ):
        raise ValueError("SOLIDWORKS native operation or profile ownership differs")
    IsCut = Operation["effect"] == "cut"
    if ("cut" in Feature["type"].lower()) != IsCut:
        raise ValueError("SOLIDWORKS native add or cut feature identity differs")
    End = Operation["end"]
    Sketch = next(
        Sketch for Sketch in Observed["sketches"] if Sketch["name"] == "RecipeProfile"
    )
    Normal = Sketch["normal_world"]
    Target = ProfileWorld(CaseValue["options"]["basis"], [0, 0, 1])
    Alignment = sum(
        First * Second for First, Second in zip(Normal, Target, strict=True)
    )
    if len(Normal) != 3 or not isclose(abs(Alignment), 1, rel_tol=0, abs_tol=1e-8):
        raise ValueError("SOLIDWORKS actual sketch normal differs from the basis")
    FrameFlip = Operation["kind"] == "extrude" and Alignment < 0
    Expected = {
        "reverse_direction": (CaseValue["options"]["direction"] == -1)
        != (FrameFlip and End["kind"] != "midplane"),
        "merge": Operation["effect"] == "join",
        "thin": Operation["thin"] is not None,
    }
    Numbers = {}
    if Operation["kind"] == "extrude":
        Start = Operation["start"]
        Expected.update(
            end1={"blind": 0, "two_direction": 0, "midplane": 6, "up_to_plane": 4}[
                End["kind"]
            ],
            both_directions=End["kind"] == "two_direction",
            from_type=3 if Start["kind"] == "offset" else 0,
        )
        if End["kind"] != "up_to_plane":
            Numbers["depth1_m"] = End["depth1_mm"] / 1000
        if End["kind"] == "two_direction":
            Expected["end2"] = 0
            Numbers["depth2_m"] = End["depth2_mm"] / 1000
        if Start["kind"] == "offset":
            Expected["offset_reverse"] = Start["reverse"] != FrameFlip
            Numbers["offset_m"] = Start["offset_mm"] / 1000
        if End["kind"] == "up_to_plane" and (
            Reading["end_reference_name"] != "EndPlane"
            or "EndPlane" not in Feature["parents"]
        ):
            raise ValueError("SOLIDWORKS extrusion lost its live end plane dependency")
    else:
        Types = {"blind": {0, 3}, "two_direction": {2, 5}, "midplane": {1, 4}}
        if Reading["type"] not in Types[End["kind"]] or Reading["axis_type"] not in (
            10,
            24,
        ):
            raise ValueError("SOLIDWORKS revolution type or sketch axis differs")
        Numbers["angle1_rad"] = radians(Operation["angle1_deg"])
        if End["kind"] == "two_direction":
            Numbers["angle2_rad"] = radians(Operation["angle2_deg"])
    if Operation["thin"] is not None:
        Thin = Operation["thin"]
        Expected["thin_type"] = 2 if Thin["side"] == "midplane" else 0
        Numbers["thickness1_m"] = Thin["thickness_mm"] / 1000
    if any(Reading[Name] != Value for Name, Value in Expected.items()) or any(
        not isclose(Reading[Name], Value, rel_tol=1e-9, abs_tol=1e-9)
        for Name, Value in Numbers.items()
    ):
        raise ValueError(
            "SOLIDWORKS actual native feature options differ from compiled operation"
        )
