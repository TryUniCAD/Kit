# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import math
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "DistinctMaterialAppearances"))
import AppearanceRequest as Appearance

SCHEMA = 1
SCOPE = "fixed_cuboid_body_texture_placement"
OPEN_SCOPE = [name for name in Appearance.OPEN_SCOPE if name != "saved_procedural_mapping"] + [
    "other_saved_procedural_mapping_and_historical_texture_bounds",
    "ogs_texture_mapping_and_rendering",
]
require = Appearance.require


def origin_point(value):
    require(
        type(value) is list
        and len(value) == 3
        and all(type(cell) is float and math.isfinite(cell) for cell in value),
        "wood_origin_cm requires three finite binary64 coordinates",
    )
    return tuple(value)


def origin_bits(origin):
    return struct.pack("<3d", *origin)


def validate(request):
    Appearance.Material.exact_fields(
        request, ("schema", "scope", "appearance_request", "wood_origin_cm"), "request"
    )
    require(
        type(request["schema"]) is int and request["schema"] == SCHEMA and request["scope"] == SCOPE,
        "Unsupported Design texture placement request schema",
    )
    Appearance.validate(request["appearance_request"])
    return request["appearance_request"], origin_point(request["wood_origin_cm"])
