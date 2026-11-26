# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import json
import sys
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import convert
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.GraphicsCodec.EmitGraphics import EmitGraphics
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.BodyChild import BodyChild
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.BrepWorld import BrepWorld
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.GroupValue import GroupValue
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.LodValue import LodValue
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.NodePayload import NodePayload
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.NodeValue import NodeValue
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.SceneWorld import SceneWorld
from convert.Formats.Fusion.GraphicsCodec.Model.State.GraphicScene import GraphicScene
from convert.Formats.Fusion.GraphicsCodec.Model.State.SceneGlobals import SceneGlobals
from convert.Formats.Fusion.GraphicsCodec.Model.State.SceneObject import SceneObject
from convert.Formats.Fusion.GraphicsCodec.Model.Values.EntityRef import EntityRef
from convert.Formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef
from convert.Formats.Fusion.GraphicsCodec.Model.Values.SceneSet import SceneSet
from convert.Formats.Fusion.GraphicsCodec.ReadGraphics import ReadGraphics
from convert.Formats.Fusion.GraphicsCodec.Schema.GlobalVersions import KGlobalVersions, KOptionalVersions
from convert.Formats.Fusion.GraphicsCodec.Validation.SceneTargets import SceneTargets

from BuildLeafPlan import leaf_plan

PROJECTION_REFUSAL = "Native fixed rectangle parameter index disagrees with its table"


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def expect_refusal(action, expected):
    try:
        action()
    except ValueError as error:
        require(str(error) == expected, f"Unexpected refusal: {error}")
        return str(error)
    raise ValueError(f"Expected refusal: {expected}")


def structural_world(plan, target, handle):
    empty = NodePayload(0, None)

    def leaves(kind):
        return tuple(LodValue(empty, 0, None, row["bounds_cm"], False) for row in plan[kind])

    # This codec-only contrast intentionally has no leaf NodeValue or selection data.
    world = BrepWorld(
        BodyChild(None, empty),
        leaves("edges"),
        BodyChild(None, empty),
        leaves("faces"),
        plan["aggregate_box_cm"],
    )
    node = NodeValue(
        2,
        None,
        SceneSet(3, ExternalRef=target),
        1,
        target,
        0.0,
        None,
        None,
        0.0,
        0,
        (0.0, 0.0, 0.0, 1.0),
        0,
        0,
        0,
        0,
    )
    group = GroupValue(None, True, None, True, 1, world, NodePayload(6, node))
    versions = tuple(
        (name, values[0]) for name, values in sorted(KGlobalVersions.items()) if name not in KOptionalVersions
    )
    return GraphicScene(
        SceneGlobals(versions, "RiverRubicon"),
        SceneWorld("ARenderList", 5, 1, (handle,), None),
        (SceneObject(handle, group),),
    )


def probe(path, expected_digest):
    raw = Path(path).read_bytes()
    require(sha256(raw).hexdigest() == expected_digest, "Candidate archive digest differs")
    public = convert.open_document(raw, source_format="f3d")
    require(
        set(public.metadata) == {"fusion.native_state"}
        and public.metadata["fusion.native_state"]["version"] == 1,
        "Expected the strict constructor-profile archive",
    )
    document = ReadDocument(raw)
    require(
        document.Graphics is None
        and not document.Snapshots
        and not document.Configurations
        and len(document.Bodies) == 1
        and isinstance(document.Bodies[0].History, PrismHistory),
        "Expected one constructor prism without a saved scene",
    )
    history = document.Bodies[0].History
    graph = BuildGraph(document)
    context = SelectExtrusion(graph)
    body = context.BodyNode
    target = EntityRef(body.SegmentId, body.ObjectId)
    require(
        graph.Resolve(context.DcBody.Fields["rBody"]) == body
        and body.Fields["actIdentifier"] == f"{body.SegmentId}_{body.ObjectId}",
        "Fresh extrusion body references disagree",
    )
    # One object has one local handle. This encoding is a probe ID policy, not a native identity rule.
    handle = ObjectRef("GroupNode", f"{body.ObjectId:016X}")
    plan = leaf_plan(history.Model)
    scene = structural_world(plan, target, handle)
    wire = EmitGraphics(scene)
    require(
        not wire.MeshStreams and not wire.FusionStreams and ReadGraphics(wire.WorldData, (), ()) == scene,
        "Structural scene failed its exact codec round trip",
    )
    act_segment = graph.OneClass("ACTTable", 1).SegmentId
    require(
        SceneTargets(scene, act_segment) == (target,), "Structural scene references another document entity"
    )
    with_scene = replace(document, Graphics=scene)
    in_memory = EmitParsed(with_scene)
    require(
        ReadDocument(in_memory) == with_scene, "Document codec changed the typed scene or constructor state"
    )
    projection_refusal = expect_refusal(
        lambda: convert.open_document(in_memory, source_format="f3d"), PROJECTION_REFUSAL
    )
    missing = max(object_id for segment, object_id in graph.Nodes if segment == target.SegmentId) + 1
    dangling = structural_world(plan, EntityRef(target.SegmentId, missing), handle)
    target_refusal = expect_refusal(
        lambda: EmitParsed(replace(document, Graphics=dangling)),
        "Graphics references an absent document entity",
    )
    return {
        "candidate_sha256": expected_digest,
        "body_entity": [target.SegmentId, target.ObjectId],
        "asm_body_key": history.Identity.BodyKey,
        "face_count": len(plan["faces"]),
        "edge_count": len(plan["edges"]),
        "world_bytes": len(wire.WorldData),
        "world_sha256": sha256(wire.WorldData).hexdigest(),
        "strict_projection_refusal": projection_refusal,
        "invalid_entity_refusal": target_refusal,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Measure a structural graphics codec boundary on generated cuboids"
    )
    parser.add_argument(
        "--case", nargs=2, metavar=("GENERATED_ARCHIVE", "SHA256"), action="append", required=True
    )
    args = parser.parse_args()
    try:
        report = {
            "cases": [probe(path, digest) for path, digest in args.case],
            "graphics_output": False,
            "native_acceptance": "unmeasured",
            "scope": "structural codec and public projection contrast",
        }
        sys.stdout.buffer.write(
            (json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
        )
    except (OSError, KeyError, TypeError, ValueError) as error:
        parser.exit(1, f"Fusion scene wire probe refused: {error}\n")


if __name__ == "__main__":
    main()
