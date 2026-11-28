"""Replay archived P03 constraints through the existing SOLIDWORKS logical Boss."""

from argparse import ArgumentParser
from hashlib import sha256
from json import dumps
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [
    str(ROOT / "src"),
    str(ROOT / "re/automation"),
    str(ROOT / "re/solidworks/WriterResearch"),
]

from ApplicationWorkers.ApplicationProtocol import write_new
from BossInput import ProjectBoss
from PairedCaptureIntake import GitSnapshot, recipe_roster, require
from P03ConstraintGraph import project_source
from RectanglePairBoss import solidworks_boss
from RectanglePairEvidence import (
    REVISION,
    SPECIFICATION,
    SPECIFICATION_SHA256,
    capture,
    load_public,
)
from interchange.document.Models.DocumentModel import CadDocument


def pinned_source():
    snapshot = GitSnapshot(ROOT)
    recipe_data = snapshot.blob(REVISION, SPECIFICATION)
    require(
        sha256(recipe_data).hexdigest() == SPECIFICATION_SHA256,
        "P03 recipe digest changed",
    )
    spec = snapshot.parse_document(recipe_data, SPECIFICATION)
    _, assets, observations = capture(
        snapshot, recipe_roster(spec)["P03"], "solidworks", spec
    )
    require(
        observations["baseline-a"][0] == "separate_process_reopen",
        "P03 source lacks its independent reopen",
    )
    raw, document = load_public(snapshot, assets["baseline-a"], "solidworks")
    (sketch,) = document.sketches
    (frame,) = [
        plane.transform
        for plane in document.support_planes
        if plane.id == sketch.support_plane_id
    ]
    solidworks_boss(document, sketch, frame, raw, spec["comparison_tolerances"])
    return document


def logical_summary(document):
    logical = ProjectBoss(document)
    return {
        "owner": logical.SketchFeatureId,
        "boss": logical.FeatureId,
        "body": logical.BodyId,
        "origin": logical.Profile.OriginId,
        "corners_mm": logical.Profile.CornersMm,
        "source_edge_slots": {
            edge.SourceId: edge.SourceSlots for edge in logical.Profile.Edges
        },
        "width": [
            logical.Width.Length.ParameterId,
            logical.Width.RelationId,
            logical.Width.PointSlots,
            logical.Width.Length.Millimetres,
        ],
        "height": [
            logical.Height.Length.ParameterId,
            logical.Height.RelationId,
            logical.Height.PointSlots,
            logical.Height.Length.Millimetres,
        ],
        "depth_mm": logical.Depth.Millimetres,
        "ordered_solver_relations": [
            [
                row.id,
                row.kind,
                [(ref.entity_id, ref.point) for ref in row.references],
                row.parameter_id,
            ]
            for row in document.sketches[0].constraints
            if not row.attributes.get("inferred")
        ],
    }


def main():
    parser = ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("capture").add_argument("--output", type=Path, required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--input", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    commands.add_parser("replay").add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    if args.action != "replay" and (args.output.exists() or args.output.is_symlink()):
        raise FileExistsError("P03 output already exists")
    if args.action == "capture":
        write_new(args.output, (pinned_source().to_json() + "\n").encode("utf-8"))
        return
    supplied = args.input.read_bytes()
    document = CadDocument.from_json(supplied.decode("utf-8"))
    if args.action == "replay":
        print(dumps(logical_summary(document), sort_keys=True, allow_nan=False))
        return
    projected, evidence = project_source(document)
    reference = pinned_source()
    require(
        document.to_json() == reference.to_json(),
        "P03 source JSON differs from the exact pinned strict read",
    )
    result = logical_summary(projected)
    payload = (projected.to_json() + "\n").encode("utf-8")
    require(
        logical_summary(CadDocument.from_json(payload.decode("utf-8"))) == result,
        "P03 logical input changed during JSON replay",
    )
    require(
        args.input.read_bytes() == supplied, "P03 source JSON changed during projection"
    )
    write_new(args.output, payload)
    evidence.update(
        {
            "capture_revision": REVISION,
            "input_sha256": sha256(supplied).hexdigest(),
            "prepared_sha256": sha256(payload).hexdigest(),
            "logical": result,
        }
    )
    print(dumps(evidence, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    try:
        main()
    except (AttributeError, KeyError, TypeError, ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
