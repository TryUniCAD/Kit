# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
import math
import struct
import sys
from fractions import Fraction
from pathlib import Path

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import PointCoords, SeriesItems

RESEARCH = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(RESEARCH / "SavedParameterBindings"), str(RESEARCH)]
from BindingRequest import OPEN_SCOPE as PARAMETER_OPEN_SCOPE
from BindingRequest import extract, validate as validate_cuboid
from GenerateSemantic import exact_fields, label, number, require
from SavedParameterBindings.PrepareRequest import open_saved

SCOPE = "fixed_cuboid_named_cameras"
SCHEMA = 1
OPEN_SCOPE = [item for item in PARAMETER_OPEN_SCOPE if item != "saved_camera_views"] + [
    "active_viewport_and_home_camera",
    "unqualified_named_camera_modes",
]
BOOLEAN_FIELDS = {
    "auto_focus": ("autoFocus", True),
    "depth_field_enabled": ("depthFieldEnabled", False),
    "mirror_x": ("mirrorX", False),
    "mirror_y": ("mirrorY", False),
}
FLOAT_FIELDS = {
    "clip_far": "clipFar",
    "clip_near": "clipNear",
    "exposure": "exposure",
    "extents_height": "extentsHeight",
    "extents_width": "extentsWidth",
    "focal_distance": "focalDistance",
    "lens_radius": "lensRadius",
    "perspective_angle": "perspectiveAngle",
}
FLOAT32_FIELDS = {"exposure", "focal_distance", "lens_radius"}
VECTORS = ("position", "target", "up")
CAMERA_FIELDS = (*BOOLEAN_FIELDS, *FLOAT_FIELDS, *VECTORS, "projection")


def require_camera_frame(position, target, up):
    endpoints = tuple(zip(target, position, strict=True))
    require(
        all(math.isfinite(end - eye) for end, eye in endpoints),
        "Named camera reference direction must be finite",
    )
    dx, dy, dz = (Fraction(end) - Fraction(eye) for end, eye in endpoints)
    up_x, up_y, up_z = map(Fraction, up)
    require(
        dx * up_y != dy * up_x or dx * up_z != dz * up_x or dy * up_z != dz * up_y,
        "Named camera view direction and up must span a plane",
    )


def camera_value(fields):
    exact_fields(fields, CAMERA_FIELDS, "camera")
    result = {}
    for key, (_, expected) in BOOLEAN_FIELDS.items():
        require(fields[key] is expected, f"Unsupported named camera {key}; expected {str(expected).lower()}")
        result[key] = expected
    require(
        type(fields["projection"]) is int and fields["projection"] == 1,
        "Unsupported named camera projection; expected stored code 1",
    )
    result["projection"] = 1
    for key in FLOAT_FIELDS:
        value = number(fields[key], f"camera.{key}")
        if key in FLOAT32_FIELDS:
            try:
                supported = struct.pack("<d", value) == struct.pack(
                    "<d", struct.unpack("<f", struct.pack("<f", value))[0]
                )
            except (OverflowError, struct.error):
                supported = False
            require(supported, f"Named camera {key} must round-trip exactly as a finite float32")
        result[key] = value
    require(0 <= result["clip_near"] < result["clip_far"], "Named camera clipping interval is invalid")
    require(
        min(
            result["extents_height"],
            result["extents_width"],
            result["focal_distance"],
            result["perspective_angle"],
        )
        > 0
        and result["lens_radius"] >= 0,
        "Named camera extents, focus, angle or lens range is invalid",
    )
    for key in VECTORS:
        point = fields[key]
        require(
            type(point) is list and len(point) == 3,
            f"Named camera {key} must be a three-element coordinate array",
        )
        result[key] = [number(value, f"camera.{key}") for value in point]
    require_camera_frame(result["position"], result["target"], result["up"])
    return result


def validate(request):
    exact_fields(request, ("schema", "scope", "cuboid", "named_views"), "request")
    require(
        type(request["schema"]) is int and request["schema"] == SCHEMA and request["scope"] == SCOPE,
        "Unsupported named-camera request schema",
    )
    validate_cuboid(request["cuboid"])
    require(type(request["named_views"]) is list, "Named views must be an explicit ordered array")
    names = set()
    views = []
    for view in request["named_views"]:
        exact_fields(view, ("name", "allow_modify", "camera"), "named view")
        name = label(view["name"], "named view name")
        require(name not in names, "Named views require unique names")
        require(view["allow_modify"] is False, "Only named views with allow_modify=false are supported")
        names.add(name)
        views.append({"name": name, "allow_modify": False, "camera": camera_value(view["camera"])})
    return {**request, "named_views": views}


def camera_fields(camera):
    return {
        **{native: camera[semantic] for semantic, (native, _) in BOOLEAN_FIELDS.items()},
        **{native: camera[semantic] for semantic, native in FLOAT_FIELDS.items()},
        **{role: dict(zip(("x", "y", "z"), camera[role], strict=True)) for role in VECTORS},
        "projection": camera["projection"],
    }


def projected_camera(fields):
    expected = (
        *[native for native, _ in BOOLEAN_FIELDS.values()],
        *FLOAT_FIELDS.values(),
        *VECTORS,
        "projection",
    )
    exact_fields(fields, expected, "native camera")
    return {
        **{semantic: fields[native] for semantic, (native, _) in BOOLEAN_FIELDS.items()},
        **{semantic: fields[native] for semantic, native in FLOAT_FIELDS.items()},
        **{role: list(PointCoords(fields[role])) for role in VECTORS},
        "projection": fields["projection"],
    }


def plain_frame(node):
    return node.Frame.RootId == "" and node.Frame.Subjects is None and node.Frame.Metadata is None


def named_views(model):
    graph = BuildGraph(model)
    settings = graph.OneClass("CommonDataAssetSettings")
    require(
        settings.Fields["curDisplayViewPorts"] == "" and not SeriesItems(settings.Fields["ViewPortsDim"]),
        "Active viewport data lies outside named-camera scope",
    )
    container = ResolveField(graph, settings, "namedViews", "NamedViews")
    require(
        container == graph.OneClass("NamedViews")
        and container.Fields["rParent"] is None
        and plain_frame(container),
        "Unsupported named-view collection owner",
    )
    selected = LinkedNodes(graph, container, "children")
    owned = {row.Identity for row in selected}
    require(
        len(selected) == len(owned)
        and owned == {row.Identity for row in graph.Nodes.values() if row.ClassName == "NamedView"},
        "Named-view collection has missing or repeated ownership",
    )
    targets = set()
    result = []
    for row in selected:
        require(
            row.ClassName == "NamedView"
            and row.SegmentId == container.SegmentId
            and plain_frame(row)
            and graph.Resolve(row.Fields["rParent"]) == container,
            "Named view has a foreign owner",
        )
        exact_fields(row.Fields, ("rParent", "m_name", "m_bEnableModify", "m_rCamera"), "native named view")
        camera = ResolveField(graph, row, "m_rCamera", "Camera")
        require(
            camera.SegmentId == row.SegmentId and camera.Identity not in targets and plain_frame(camera),
            "Named camera is shared or belongs to a foreign graph",
        )
        targets.add(camera.Identity)
        result.append(
            {
                "name": row.Fields["m_name"],
                "allow_modify": row.Fields["m_bEnableModify"],
                "camera": projected_camera(camera.Fields),
            }
        )
    require(
        targets == {row.Identity for row in graph.Nodes.values() if row.ClassName == "Camera"},
        "Named-camera graph contains an unowned camera",
    )
    return result


def projection(model, public):
    return validate(
        {
            "schema": SCHEMA,
            "scope": SCOPE,
            "cuboid": extract(model, public),
            "named_views": named_views(model),
        }
    )


def prepare(source):
    return projection(*open_saved(source))


def canonical_views(views):
    return json.dumps(views, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
