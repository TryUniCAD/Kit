import argparse
from dataclasses import replace
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import subprocess
import sys

from convert import open_document
from convert.adapters.Fusion.State.DecodeState import DecodeState
from convert.Formats.Fusion.BrepCodec.Prism.Validation.CheckPrismFrame import (
    CheckPrismFrame,
)
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.GraphicsCodec.EmitGraphics import EmitGraphics
from convert.Formats.Fusion.GraphicsCodec.ReadGraphics import ReadGraphics
from convert.Formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KEdgeCorners,
    KFaceCorners,
)
from interchange import CadDocument

from BuildDisplayOrderContrast import display_roles, display_world, require, role_box
from PrismFramePrediction import predict


def checked_scene(scene):
    encoded = EmitGraphics(scene)
    decoded = ReadGraphics(
        encoded.WorldData, encoded.MeshStreams, encoded.FusionStreams
    )
    require(decoded == scene, "encoded scene did not preserve typed values")
    return encoded


def rebuild_leaves(model, height_mm):
    require(len(model.Bodies) == 1, "expected one live solid")
    history = model.Bodies[0].History
    body = replace(history.Model, Height=height_mm)
    original = history.Frame
    result = predict(original, height_mm / 10)
    CheckPrismFrame(body, result)
    owner, world = display_world(model)

    def update(nodes, groups):
        roles = display_roles(nodes, owner, original.CornersCm, groups)
        return tuple(
            replace(node, Bounds=role_box(result.CornersCm, groups[role]))
            for node, role in zip(nodes, roles, strict=True)
        )

    edges = update(world.EdgeNodes, KEdgeCorners)
    faces = update(world.FaceNodes, KFaceCorners)
    rebuilt_world = replace(world, EdgeNodes=edges, FaceNodes=faces)
    scene = model.Graphics
    rebuilt_scene = replace(
        scene,
        Objects=tuple(
            (
                replace(item, Value=replace(item.Value, WorldValue=rebuilt_world))
                if getattr(item.Value, "WorldValue", None) is world
                else item
            )
            for item in scene.Objects
        ),
    )
    require(rebuilt_scene != scene, "height did not change the saved scene")
    for groups, old, fresh in (
        (KEdgeCorners, world.EdgeNodes, edges),
        (KFaceCorners, world.FaceNodes, faces),
    ):
        roles = display_roles(fresh, owner, result.CornersCm, groups)
        require(
            roles == display_roles(old, owner, original.CornersCm, groups),
            "graphics leaves changed role",
        )
        if any(
            before.Bounds != after.Bounds
            for before, after in zip(old, fresh, strict=True)
        ):
            try:
                display_roles(old, owner, result.CornersCm, groups)
            except ValueError:
                pass
            else:
                raise ValueError("stale leaf bounds passed the changed frame")
    require(rebuilt_world.ModelBox == world.ModelBox, "out-of-scope aggregate changed")
    original_bytes = checked_scene(scene)
    rebuilt_bytes = checked_scene(rebuilt_scene)
    require(
        original_bytes.MeshStreams == rebuilt_bytes.MeshStreams,
        "unaffected mesh stream changed",
    )
    require(
        original_bytes.FusionStreams == rebuilt_bytes.FusionStreams,
        "unaffected stream changed",
    )
    return {
        "role_sequence": [
            display_roles(edges, owner, result.CornersCm, KEdgeCorners),
            display_roles(faces, owner, result.CornersCm, KFaceCorners),
        ],
        "groups": [
            [item.Bounds for item in edges],
            [item.Bounds for item in faces],
        ],
        "world_sha256": sha256(rebuilt_bytes.WorldData).hexdigest(),
        "old_world_sha256": sha256(original_bytes.WorldData).hexdigest(),
        "aggregate_cm": world.ModelBox,
        "body_dimensions_mm": [body.Width, body.Depth, body.Height],
        "face_attribute_set_count": len(
            {repr(node.NodeData.DataValue.Attributes) for node in faces}
        ),
    }


def child(persisted, height_mm):
    def block_native_file_open(event, args):
        if event == "open" and isinstance(args[0], (str, bytes)):
            filename = (
                args[0].decode(errors="replace")
                if isinstance(args[0], bytes)
                else args[0]
            )
            if filename.lower().endswith(".f3d"):
                raise RuntimeError(
                    "native archive access is forbidden in the predictor"
                )

    sys.addaudithook(block_native_file_open)
    document = CadDocument.from_json(persisted.read_text(encoding="utf-8"))
    require(
        document.metadata.get("fusion.read_only") is True,
        "expected read-only saved source",
    )
    state = document.metadata["fusion.native_state"]
    require(state["version"] == 2, "expected typed saved state 2")
    model = DecodeState(state["model"])
    return rebuild_leaves(model, height_mm)


def compare(source, control, height_mm, output):
    original = source.read_bytes()
    output.mkdir()
    persisted = output / "Document.json"
    persisted.write_text(
        open_document(original, source_format="f3d", strict=True).to_json(),
        encoding="utf-8",
    )
    worker = subprocess.run(
        (
            sys.executable,
            "-B",
            str(Path(__file__).resolve()),
            "--persisted",
            str(persisted.resolve()),
            "--height-mm",
            str(height_mm),
        ),
        capture_output=True,
        text=True,
        timeout=90,
        cwd=output,
    )
    if worker.returncode:
        (output / "PredictorError.txt").write_text(worker.stderr, encoding="utf-8")
        raise ValueError("offline predictor refused the source")
    report = json.loads(worker.stdout)
    actual = control.read_bytes()
    require(
        sha256(original).digest() != sha256(actual).digest(),
        "require separate saved control",
    )
    measured = ReadDocument(actual)
    owner, world = display_world(measured)
    history = measured.Bodies[0].History
    actual_dimensions = [history.Model.Width, history.Model.Depth, history.Model.Height]
    require(
        actual_dimensions == report["body_dimensions_mm"],
        "native control changes a dimension outside the planned height edit",
    )
    groups = (world.EdgeNodes, world.FaceNodes)
    corners = (KEdgeCorners, KFaceCorners)
    measured_roles = [
        display_roles(items, owner, history.Frame.CornersCm, keys)
        for items, keys in zip(groups, corners, strict=True)
    ]
    observed = [[node.Bounds for node in nodes] for nodes in groups]

    def by_role(role_groups, box_groups):
        return [
            sorted(zip(roles, boxes, strict=True))
            for roles, boxes in zip(role_groups, box_groups, strict=True)
        ]

    expected_roles = by_role(report["role_sequence"], report["groups"])
    observed_roles = by_role(
        measured_roles, [[list(box) for box in nodes] for nodes in observed]
    )
    require(
        expected_roles == observed_roles,
        "generated leaf geometry differs from the native control",
    )
    report.update(
        source_sha256=sha256(original).hexdigest(),
        measured_sha256=sha256(actual).hexdigest(),
        same_order=report["role_sequence"] == [list(roles) for roles in measured_roles],
        measured_aggregate_cm=world.ModelBox,
        role_matched_leaf_bounds=True,
    )
    (output / "Report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Compare JSON-derived graphics leaf bounds with a saved height edit"
    )
    parser.add_argument("--height-mm", type=float, required=True)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--source", type=Path)
    inputs.add_argument("--persisted", type=Path)
    parser.add_argument("--control", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not isfinite(args.height_mm) or args.height_mm <= 0:
        parser.error("height must be positive and finite")
    if args.persisted:
        print(
            json.dumps(
                child(args.persisted, args.height_mm),
                separators=(",", ":"),
                allow_nan=False,
            )
        )
        return
    if args.control is None or args.output is None:
        parser.error("a saved control and new output directory are required")
    compare(args.source, args.control, args.height_mm, args.output)


if __name__ == "__main__":
    main()
