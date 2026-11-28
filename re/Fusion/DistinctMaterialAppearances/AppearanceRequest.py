# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
import sys
from dataclasses import replace
from pathlib import Path

from convert.Formats.Fusion.DocumentCodec.Materials.CheckMaterial import CheckMaterial
from convert.Formats.Fusion.DocumentCodec.Materials.CheckParts import CheckColor, CheckParts
from convert.Formats.Fusion.DocumentCodec.Materials.Model.FinishSpec import FinishSpec

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "SavedMaterialProperties"))
import MaterialRequest as Material

SCHEMA = 1
SCOPE = "fixed_cuboid_distinct_material_appearances"
OPEN_SCOPE = Material.OPEN_SCOPE
require = Material.require


def validate(request):
    Material.exact_fields(
        request, ("schema", "scope", "material_request", "physical_appearance_rgba", "body_finish"), "request"
    )
    require(
        type(request["schema"]) is int and request["schema"] == SCHEMA and request["scope"] == SCOPE,
        "Unsupported distinct material appearance request schema",
    )
    configuration, material, component_default = Material.validate(request["material_request"])
    body = request["body_finish"]
    require(type(body) is dict and body.get("kind") in ("metal", "opaque"), "Unsupported body finish family")
    body_finish = Material.finish_spec(body, body["kind"] == "metal")
    physical_color = Material.rgba(request["physical_appearance_rgba"], "physical_appearance_rgba")
    physical = replace(material, Color=physical_color)
    CheckColor(material.Color)
    CheckParts(body_finish, FinishSpec)
    CheckMaterial(physical)
    return configuration, physical, component_default, material.Color, body_finish


def finish_record(finish):
    result = {
        "name": finish.NameValue,
        "kind": "metal" if finish.Metallic else "opaque",
        "color_space": finish.ColorSpace,
        "tint_rgba": Material.channels(finish.Tint),
        **Material.projected_numbers(finish, Material.FINISH),
    }
    if not finish.Metallic:
        result.update(
            reflectance=finish.Reflectance,
            translucent=finish.Translucent,
            scatter_distance_mm=finish.ScatterDistance,
            scatter_color_rgba=Material.channels(finish.ScatterColor),
        )
    return result


def fingerprint(physical, default, body_color, body_finish):
    return json.dumps(
        {
            "physical": Material.material_properties(physical, default),
            "physical_appearance_rgba": Material.channels(physical.Color),
            "body_rgba": Material.channels(body_color),
            "body_finish": finish_record(body_finish),
        },
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
