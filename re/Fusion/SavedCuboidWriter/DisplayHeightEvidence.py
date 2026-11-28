# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of the
# PolyForm Strict License 1.0.0 and voids all licenses granted to you
# under it immediately and permanently.

import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from struct import unpack_from
from zipfile import ZipFile

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.BrepCodec.Prism.Reading.ReadPrismGraph import ReadPrismGraph
from convert.Formats.Fusion.BrepCodec.Prism.Reading.ReadPrismRoles import ReadPrismRoles
from convert.Formats.Fusion.BrepCodec.Prism.Reading.ReadPrismWire import ReadPrismWire
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.GeometryCodec.Prism.PrismLayout import KEdgeCorners, KFaceCorners
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.BrepWorld import BrepWorld
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.GroupValue import GroupValue
from convert.Formats.Fusion.GraphicsCodec.Model.Values.EntityRef import EntityRef


def archive_roles(payload):
    with ZipFile(BytesIO(payload)) as archive:
        histories = [name for name in archive.namelist() if name.endswith(".smbh")]
        if len(histories) != 1:
            raise ValueError("This audit requires one cuboid history stream")
        wire = ReadPrismWire(archive.read(histories[0]))
    roles = ReadPrismRoles(ReadPrismGraph(wire.Table))
    return {
        "edges": tuple(roles.Edges[identity] for identity in sorted(roles.Edges)),
        "faces": tuple(roles.Faces[identity] for identity in sorted(roles.Faces)),
    }


def box(points):
    coordinates = tuple(zip(*points, strict=True))
    return tuple(map(min, coordinates)) + tuple(map(max, coordinates))


def role_boxes(corners, groups):
    return tuple(box([corners[index] for index in group]) for group in groups)


def owned_world(model):
    context = SelectExtrusion(BuildGraph(model))
    target = EntityRef(context.BodyNode.SegmentId, context.BodyNode.ObjectId)
    if model.Graphics is None:
        raise ValueError("This audit requires a saved solid graphics scene")
    candidates = []
    for item in model.Graphics.Objects:
        group = item.Value
        if not isinstance(group, GroupValue) or not isinstance(group.WorldValue, BrepWorld):
            continue
        data = group.NodeData.DataValue
        if data is not None and data.EntityLink == target:
            candidates.append(group.WorldValue)
    if len(candidates) != 1:
        raise ValueError("Expected one solid graphics world linked to the active body")
    return target, candidates[0]


def check_nodes(target, nodes, expected):
    if len(nodes) != len(expected) or len(set(expected)) != len(expected):
        raise ValueError("Display nodes do not form the complete scoped topology")
    data = tuple(node.NodeData.DataValue for node in nodes)
    if any(entry is None or entry.EntityLink != target for entry in data):
        raise ValueError("Display node does not reference its solid body")
    if any(node.Geometry is not None or node.LodMask != 0 for node in nodes):
        raise ValueError("This audit only qualifies zero-LOD boxes")
    facing = tuple(expected.index(node.Bounds) for node in nodes)
    if len(set(facing)) != len(expected):
        raise ValueError("Display nodes alias a solved topology role")
    return facing, tuple(entry.Qualifier for entry in data)


def inspect(path):
    payload = path.read_bytes()
    model = ReadDocument(payload)
    if len(model.Bodies) != 1:
        raise ValueError("Expected one saved cuboid body")
    target, world = owned_world(model)
    frame = model.Bodies[0].History.Frame
    corners = frame.CornersCm
    edge_order, edge_qualifiers = check_nodes(target, world.EdgeNodes, role_boxes(corners, KEdgeCorners))
    face_order, face_qualifiers = check_nodes(target, world.FaceNodes, role_boxes(corners, KFaceCorners))
    source_roles = archive_roles(payload)
    normalized = EmitParsed(model)
    normalized_roles = archive_roles(normalized)
    if ReadDocument(normalized) != model:
        raise ValueError("Normalized re-emission changes the saved typed model")
    return {
        "source_sha256": sha256(payload).hexdigest(),
        "normalized_sha256": sha256(normalized).hexdigest(),
        "modeled_box_cm": box(corners),
        "aggregate_display_box_cm": world.ModelBox,
        "display_edge_order": edge_order,
        "display_face_order": face_order,
        "edge_qualifiers_in_scene_order": edge_qualifiers,
        "face_qualifiers_in_scene_order": face_qualifiers,
        "source_physical_order": source_roles,
        "typed_face_chain_order": frame.FaceOrder,
        "normalized_physical_order": normalized_roles,
        "previews": {
            preview.Name: {
                "pixel_dimensions": unpack_from(">2I", preview.Payload, 16),
                "sha256": sha256(preview.Payload).hexdigest(),
            }
            for preview in model.Previews
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Audit saved cuboid display associations")
    parser.add_argument("--case", type=Path, action="append", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    output = [inspect(item) for item in args.case]
    with args.report.open("x", encoding="utf-8", newline="\n") as report:
        json.dump({"cases": output, "scope": "decoded display associations, no writer or native claims"}, report, indent=2)
        report.write("\n")


if __name__ == "__main__":
    main()
