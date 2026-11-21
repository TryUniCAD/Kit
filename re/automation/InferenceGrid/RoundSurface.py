# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import math

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Planar.MapPoint import MapPoint
from convert.Formats.Fusion.BrepCodec.Journal.Round.SphereNode import SphereNode
from convert.Formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry


def closed_surface(data):
    entities = ReadGeometry(data).Entities

    def one(kind):
        matches = [i for i, node in enumerate(entities) if isinstance(node, kind)]
        if len(matches) != 1:
            raise ValueError("expected one closed round solid")
        return matches[0], entities[matches[0]]

    bi, body = one(BodyNode)
    li, lump = one(LumpNode)
    si, shell = one(ShellNode)
    fi, face = one(FaceNode)
    if (
        body.FirstLump,
        lump.FirstShell,
        lump.OwnerBody,
        shell.FirstFace,
        shell.OwnerLump,
        face.OwnerShell,
    ) != (li, si, bi, fi, li, si):
        raise ValueError("round topology ownership differs")
    if (
        (lump.NextLump, shell.NextShell, shell.FirstWire, face.NextFace, face.FirstLoop)
        != (-1,) * 5
        or face.Reversed
        or face.DoubleSided
    ):
        raise ValueError("expected an untrimmed single face")
    surface = entities[face.Surface]
    if not isinstance(surface, (SphereNode, TorusNode)) or any(
        v is not None
        for v in (surface.ULower, surface.UUpper, surface.VLower, surface.VUpper)
    ):
        raise ValueError("expected a complete sphere or torus")
    center = surface.CenterCm
    axis = (
        surface.AxisVector if isinstance(surface, TorusNode) else surface.PoleDirection
    )
    scale = 1.0
    if body.TransformRef != -1:
        transform = entities[body.TransformRef]
        if (
            not isinstance(transform, TransformNode)
            or transform.HasShear
            or not transform.ScaleFactor > 0
        ):
            raise ValueError("unsupported round solid placement")
        columns = (transform.ColumnX, transform.ColumnY, transform.ColumnZ)
        if any(
            not math.isclose(
                sum(a * b for a, b in zip(col, other)), float(i == j), abs_tol=1e-10
            )
            for i, col in enumerate(columns)
            for j, other in enumerate(columns)
        ):
            raise ValueError("expected orthonormal placement axes")
        center = MapPoint(transform, center)
        axis = tuple(sum(axis[j] * columns[j][i] for j in range(3)) for i in range(3))
        scale = transform.ScaleFactor
    if not math.isclose(math.hypot(*axis), 1.0, rel_tol=1e-10):
        raise ValueError("round axis is not a unit vector")
    return surface, center, axis, scale
