# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

# explicit driving names prevent captured defaults from silently defining requested geometry
KFusionDefaults = {
    "P01": {"width_mm": 40.0, "height_mm": 20.0},
    "P02": {"diameter_mm": 10.0},
    "P03": {"width_mm": 40.0, "height_mm": 20.0, "depth_mm": 10.0},
    "P04": {
        "width_mm": 40.0,
        "height_mm": 20.0,
        "depth_mm": 10.0,
        "cut_width_mm": 10.0,
        "cut_height_mm": 8.0,
        "cut_depth_mm": 4.0,
    },
    "P05": {
        "inner_radius_mm": 2.0,
        "outer_radius_mm": 6.0,
        "height_mm": 12.0,
        "angle_deg": 360.0,
    },
}

# lineage reservations must remain separate when new parameter grids are generated
KFusionModes = {
    "discovery": ("P01", "P03", "P04"),
    "qualification": ("P02",),
    "holdout": ("P05",),
}
