# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of the
# PolyForm Strict License 1.0.0 and voids all licenses granted to you
# under it immediately and permanently.

from math import isfinite

from convert.Formats.Fusion.BrepCodec.Prism.Validation.CheckPrismFrame import CheckPrismFrame
from convert.Formats.Fusion.DocumentCodec.Rectangle.CuboidFrame import CuboidFrame
from convert.Formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody
from convert.Formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KEdgeCorners,
    KFaceCorners,
    KFirstEdge,
    KFirstFace,
)


def bounds(points):
    coordinates = tuple(zip(*points, strict=True))
    return tuple(map(min, coordinates)) + tuple(map(max, coordinates))


def leaf_plan(model):
    if model.BasePoint != (0.0, 0.0, 0.0):
        raise ValueError("Derived display plan requires an origin-anchored cuboid")
    lengths = (model.Width, model.Depth, model.Height)
    if not all(type(value) in (float, int) and isfinite(value) and value > 0 for value in lengths):
        raise ValueError("Derived display plan requires positive finite dimensions")
    frame = CuboidFrame(model)
    CheckPrismFrame(model, frame)

    def plan(groups, first_slot):
        return tuple(
            {
                "role": index,
                "serialized_history_slot": first_slot + index,
                "bounds_cm": bounds([frame.CornersCm[corner] for corner in group]),
            }
            for index, group in enumerate(groups)
        )

    faces = plan(KFaceCorners, KFirstFace)
    edges = plan(KEdgeCorners, KFirstEdge)
    if (
        len(set(row["bounds_cm"] for row in faces)) != len(faces)
        or len(set(row["bounds_cm"] for row in edges)) != len(edges)
    ):
        raise ValueError("Derived display plan aliases two topology roles")
    return {
        "aggregate_box_cm": bounds(frame.CornersCm),
        "faces": faces,
        "edges": edges,
        "face_chain_roles": frame.FaceOrder,
    }
