# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

# distinct overrides exercise every registered primitive without treating defaults as independent acceptance evidence
KCompileCases = (
    ("extrude-two-direction", {"depth1_mm": 13, "depth2_mm": 7}),
    ("extrude-midplane", {"depth_mm": 16}),
    ("extrude-offset-start", {"offset_mm": -7, "depth_mm": 12}),
    ("extrude-thin", {"length_mm": 37, "thickness_mm": 3}),
    ("extrude-up-to", {"plane_z_mm": 40, "diameter_mm": 8}),
    ("revolve-two-direction", {"angle1_deg": 135, "angle2_deg": 60}),
    ("revolve-midplane", {"angle_deg": 120}),
    ("revolve-thin", {"radius_mm": 13, "thickness_mm": 3}),
    ("revolve-cut", {"inner_radius_mm": 7, "height_mm": 3}),
)

# malformed inputs must fail at compilation rather than becoming native application requests
KInvalidCases = (
    {"recipe": "invented"},
    {"recipe": "extrude-surface"},
    {"recipe": "extrude-midplane", "parameters": {"unexpected": 1}},
    {"recipe": "extrude-midplane", "parameters": {"depth_mm": True}},
    {"recipe": "extrude-midplane", "parameters": {"depth_mm": float("nan")}},
    {"recipe": "extrude-midplane", "parameters": {"depth_mm": float("inf")}},
    {"recipe": "extrude-midplane", "parameters": {"depth_mm": 0}},
    {"recipe": "extrude-midplane", "parameters": {"depth_mm": "10"}},
    {"recipe": "extrude-up-to", "parameters": {"plane_z_mm": 10}},
    {"recipe": "extrude-up-to", "parameters": {"diameter_mm": 20}},
    {
        "recipe": "revolve-two-direction",
        "parameters": {"angle1_deg": 300, "angle2_deg": 90},
    },
    {"recipe": "revolve-midplane", "parameters": {"inner_radius_mm": 21}},
    {"recipe": "revolve-cut", "parameters": {"height_mm": 10}},
    {"recipe": "revolve-cut", "parameters": {"outer_radius_mm": 11}},
    {"recipe": "revolve-thin", "options": {"basis": "XY"}},
    {"recipe": "extrude-midplane", "options": {"direction": True}},
    {"recipe": "extrude-midplane", "options": {"direction": -1}},
    {"recipe": "extrude-midplane", "options": {"unregistered": 1}},
    {"recipe": "extrude-thin", "options": {"variant": "closed-contour-thin-feature"}},
    {"recipe": "extrude-up-to", "options": {"variant": "up-to-next"}},
    {"recipe": "extrude-up-to", "options": {"variant": "up-to-vertex"}},
    {"recipe": "extrude-midplane", "options": {"program": {"schema": 1}}},
)
