# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# native consumers receive explicit typed geometry extents owners and references instead of recipe switches
def RecipeProgram(CaseValue, Descriptor):
    Parameters, Options = CaseValue["parameters"], CaseValue["options"]
    Profile = {
        "kind": Descriptor["profile"],
        "support": "plane",
        "origin_mm": [0.0, 0.0, 0.0],
    }
    if Profile["kind"] == "rectangle":
        Profile.update(
            width_mm=Parameters["width_mm"], height_mm=Parameters["height_mm"]
        )
    elif Profile["kind"] == "radial_rectangle":
        Profile.update(
            inner_radius_mm=Parameters["inner_radius_mm"],
            outer_radius_mm=Parameters["outer_radius_mm"],
            height_mm=Parameters["height_mm"],
        )
    elif Profile["kind"] == "circle":
        Profile.update(
            support="seed_top_face",
            origin_mm=[20.0, 10.0, 10.0],
            diameter_mm=Parameters["diameter_mm"],
        )
    elif Descriptor["operation"] == "revolve":
        Profile.update(
            axis="v",
            origin_mm=[Parameters["radius_mm"], 0.0, 0.0],
            radius_mm=Parameters["radius_mm"],
            length_mm=Parameters["height_mm"],
        )
    else:
        Profile.update(axis="u", length_mm=Parameters["length_mm"])
    Seed = None
    if Descriptor["seed"] == "block":
        Seed = {"kind": "block", "width_mm": 40.0, "depth_mm": 20.0, "height_mm": 10.0}
    elif Descriptor["seed"] == "cylinder":
        Seed = {"kind": "cylinder", "diameter_mm": 20.0, "height_mm": 10.0}
    Offset = Parameters.get("offset_mm", 0.0)
    Start = {
        "kind": "offset" if "offset_mm" in Parameters else "sketch_plane",
        "offset_mm": abs(Offset),
        "reverse": Offset < 0,
    }
    End = {
        "kind": Descriptor["extent"],
        "depth1_mm": Parameters.get("depth1_mm", Parameters.get("depth_mm", 0.0)),
        "depth2_mm": Parameters.get("depth2_mm", 0.0),
        "target_z_mm": Parameters.get("plane_z_mm", 0.0),
    }
    Thin = None
    if "thickness_mm" in Parameters:
        Side = (
            "outward"
            if Descriptor["operation"] == "revolve"
            else "midplane" if Options["variant"] == "midplane-wall" else "+v"
        )
        Thin = {"thickness_mm": Parameters["thickness_mm"], "side": Side}
    Operation = {
        "kind": Descriptor["operation"],
        "effect": Descriptor["effect"],
        "feature_name": "RecipeFeature",
        "start": Start,
        "end": End,
        "angle1_deg": Parameters.get("angle1_deg", Parameters.get("angle_deg", 0.0)),
        "angle2_deg": Parameters.get("angle2_deg", 0.0),
        "thin": Thin,
    }
    Bindings = {
        ParamName: {"owner": Owner, "field": Field}
        for ParamName, (Owner, Field) in Descriptor["native_fields"].items()
    }
    return {
        "schema": 1,
        "recipe_sha256": Descriptor["written_recipe_sha256"],
        "seed": Seed,
        "profile": Profile,
        "operation": Operation,
        "bindings": Bindings,
    }
