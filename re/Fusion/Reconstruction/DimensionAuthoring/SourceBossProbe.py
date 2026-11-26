# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import json
from pathlib import Path
from subprocess import check_output

from FusionNeutralRectanglePlan import (
    REVISION,
    ROOT,
    SPECIFICATION,
    SPECIFICATION_SHA256,
    VARIANTS,
    report as source_report,
)
from PairedCaptureIntake import GitSnapshot, require, sha256
from PairedPerimeters import match_perimeters
from ProbeBossAuthor import DRIVERS, generate_boss
from ProbeBossParams import inspect_parameters, inspect_sketch_rules
from ProbeBossReadback import (
    inspect_body,
    inspect_dependencies,
    inspect_selected_profile,
    rectangle_shape,
)
from RectanglePairBoss import find_boss
from RectanglePairEvidence import load_public
from RectanglePairSketch import world
from SourceRectangleProbe import candidate_edges, verify_axes, verify_drivers
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Policy.CheckScopes import CheckScopes
from interchange.geometry.Models.GeometryCurves import LineGeometry

# Pin the research side of the authoring process while retaining the shared codec revision.
PROGRAMS = (
    "SourceBossProbe.py",
    "ProbeBossAuthor.py",
    "ProbeBossParams.py",
    "ProbeBossReadback.py",
    "ProbeOrigin.py",
    "SourceRectangleProbe.py",
)


# Select only the observed first positive blind solid and preserve its native source history IDs.
def source_geometry(snapshot, case):
    _, document = load_public(snapshot, case["source"], "solidworks")
    (sketch,) = document.sketches
    boss, loop = find_boss(document, sketch)
    (plane,) = [
        row for row in document.support_planes if row.id == sketch.support_plane_id
    ]
    (body,) = document.bodies
    depth = case["boss"]["source"]
    require(
        document.source.sha256 == case["source"]["sha256"]
        and case["source"]["measurement_phase"] == "separate_process_reopen"
        and sketch.id == case["source"]["sketch_id"]
        and loop
        == tuple(case["perimeter"]["source_loop"])
        == tuple(depth["selected_entities"])
        and body.final_feature_id == boss.id
        and [row.id for row in document.feature_timeline if row.operation] == [boss.id]
        and boss.operation == depth["operation"] == "join"
        and depth["direction"] == (0.0, 0.0, 1.0)
        and depth["depth_parameter"]["name"] == DRIVERS[2],
        "Source P03 is outside the verified first-body positive XY scope",
    )
    lengths = tuple(
        case["dimensions"][name]["source"]["value_mm"] for name in DRIVERS[:2]
    )
    sizes = (*lengths, depth["signed_depth_mm"])
    entities = {row.id: row for row in sketch.entities}
    edges = []
    for identity in loop:
        line = entities[identity].geometry
        require(
            isinstance(line, LineGeometry), "Source P03 selected loop must use lines"
        )
        edges.append(
            (
                identity,
                (world(plane.transform, line.start), world(plane.transform, line.end)),
            )
        )
    return sizes, edges, body.name, boss.id


# Resolve the actual stored Boss recipe and compare it to independent source edges and body measurements.
def candidate_evidence(case, payload, sizes, edges, measured, tolerances, *, settings_ranks=(0, 1), line_normal=(0.0, 0.0, -1.0)):
    model = ReadDocument(payload)
    graph = BuildGraph(model)
    context = SelectExtrusion(graph)
    CheckScopes(graph, context, model.Asset.AssetId)
    parameters = inspect_parameters(graph, context, sizes)
    rules = inspect_sketch_rules(payload, graph, context, parameters, settings_ranks=settings_ranks)
    shape = rectangle_shape(graph, context, rules, line_normal=line_normal)
    profile = inspect_selected_profile(graph, context, shape, model.Asset.AssetId)
    target, points, frame, incidence = candidate_edges(payload, rules, graph=graph)
    tolerance = tolerances["length_mm_absolute"]
    match = match_perimeters(edges, target, tolerance)
    require(
        match["status"] == "equal",
        "The saved P03 perimeter differs from its measured source",
    )
    target_members = {identity for _, identity in match["matched_links"]}
    require(
        target_members == set(profile["ordered_line_members"])
        and rules["anchor"]["corner"]["id"] in dict(incidence)
        and rules["anchor"]["origin"]["id"] not in dict(incidence)
        and frame["sketch"] == profile["sketch"],
        "P03 Boss did not select the exact matched perimeter and anchored sketch",
    )
    drivers = {}
    for name, dimension in zip(DRIVERS[:2], rules["dimensions"], strict=True):
        drivers[name] = {
            **parameters[name],
            "value_cm": parameters[name]["value_native"],
            "dimension_id": dimension["id"],
        }
    verify_drivers(
        case,
        sizes[:2],
        {"anchor_evidence": rules, "direct_driver_inventory": {"parameters": drivers}},
        points,
    )
    axes = verify_axes(payload, case, match, frame["sketch"])
    return {
        "archive_sha256": sha256(payload),
        "archive_bytes": len(payload),
        "target_frame": frame,
        "target_anchor_and_dimensions": rules,
        "target_axis_relations": axes,
        "matched_perimeter": match,
        "target_selected_profile": profile,
        "target_parameter_inventory": parameters,
        "target_dependencies": inspect_dependencies(
            graph, context, parameters, profile
        ),
        "target_body": inspect_body(
            graph, context, model, shape, sizes, measured, tolerances
        ),
    }


# Join each output back to the exact independent reopen row and the native source bindings.
def build_case(snapshot, case, observations, tolerances):
    variant = case["variant"]
    source_name = Path(case["source"]["path"]).name
    measured = observations[source_name]
    sizes, edges, body_name, feature_id = source_geometry(snapshot, case)
    payload = generate_boss(variant, sizes, body_name)
    result = candidate_evidence(case, payload, sizes, edges, measured, tolerances)
    return payload, {
        "file": f"P03-{variant}.f3d",
        "variant": variant,
        "source": case["source"],
        "source_sketch_dimensions": {
            name: case["dimensions"][name]["source"] for name in DRIVERS[:2]
        },
        "source_origin": case["anchor"]["source_origin_coincidence"],
        "source_feature_id": feature_id,
        "source_boss": case["boss"]["source"],
        "source_reopen_observation_sha256": sha256(
            json.dumps(measured, sort_keys=True, allow_nan=False).encode()
        ),
        **result,
    }


# Reject an occupied destination before reading any inputs.
def new_output(output):
    require(not output.is_symlink(), "Use a new private output directory outside the Git checkout")
    output = output.resolve()
    require(
        not output.is_relative_to(ROOT) and not output.exists(),
        "Use a new private output directory outside the Git checkout",
    )
    return output


# Resolve measured source custody only in the modes that have the trusted Git checkout.
def read_pinned_cases():
    snapshot = GitSnapshot(ROOT)
    source = source_report()
    require(
        source["source_capture_revision"] == REVISION, "P03 source revision differs"
    )
    report_pin = source["receipts"]["P03"]
    observations = report_pin["measurements"]
    raw = snapshot.blob(REVISION, observations["path"])
    require(
        sha256(raw) == observations["sha256"],
        "P03 separate-process observations differ",
    )
    reopened = snapshot.parse_document(raw, observations["path"])["observations"][
        "reopened_files"
    ]
    spec = snapshot.blob(REVISION, SPECIFICATION)
    require(sha256(spec) == SPECIFICATION_SHA256, "P03 recipe specification differs")
    tolerances = snapshot.parse_document(spec, SPECIFICATION)["comparison_tolerances"]
    cases = [case for case in source["cases"] if case["recipe"] == "P03"]
    require(
        tuple(row["variant"] for row in cases) == VARIANTS["P03"],
        "Unexpected positive XY P03 candidate roster",
    )
    return snapshot, report_pin, reopened, tolerances, cases


# Build and verify every archive before creating a new caller-owned directory outside the checkout.
def generate_report(output):
    output = new_output(output)
    snapshot, report_pin, reopened, tolerances, cases = read_pinned_cases()
    results = [build_case(snapshot, case, reopened, tolerances) for case in cases]
    result = {
        "schema": 1,
        "scope": "private positive XY P03 source-derived first blind Boss research",
        "qualification": "candidate_requires_licensed_target_acceptance",
        "source_capture_revision": REVISION,
        "source_receipt": report_pin,
        "source_specification_sha256": SPECIFICATION_SHA256,
        "codec_revision": check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "generator_sources": {
            name: sha256(Path(__file__).with_name(name).read_bytes())
            for name in PROGRAMS
        },
        "candidates": [row for _, row in results],
    }
    encoded = (
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    output.mkdir()
    for payload, row in results:
        with (output / row["file"]).open("xb") as archive:
            archive.write(payload)
    with (output / "P03CandidateEvidence.json").open("xb") as evidence:
        evidence.write(encoded)
    return sha256(encoded)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate verified private positive XY P03 candidates"
    )
    parser.add_argument("--output", type=Path, required=True)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--request", type=Path)
    parser.add_argument("--source-json", type=Path)
    parser.add_argument("--logical-json", type=Path)
    parser.add_argument("--request-sha256")
    parser.add_argument("--source-witness", type=Path)
    parser.add_argument("--source-witness-sha256")
    parser.add_argument("--seed-helper", type=Path)
    parser.add_argument("--snapshot-builder", type=Path)
    parser.add_argument("--snapshot-owners", type=Path)
    parser.add_argument("--written-at", type=int)
    args = parser.parse_args()
    prepare = (args.source_json, args.logical_json)
    replay = (args.request_sha256, args.source_witness, args.source_witness_sha256,
              args.seed_helper, args.snapshot_builder, args.snapshot_owners, args.written_at)
    try:
        if args.prepare and all(value is not None for value in prepare) and all(value is None for value in replay):
            from SourceBossReplay import prepare_output

            print(json.dumps(prepare_output(args.output, *prepare), sort_keys=True))
        elif args.request is not None and all(value is not None for value in replay) and all(value is None for value in prepare):
            from SourceBossReplay import replay_output

            print(json.dumps(replay_output(args.output, args.request, *replay), sort_keys=True))
        elif not args.prepare and args.request is None and all(value is None for value in (*prepare, *replay)):
            print(generate_report(args.output))
        else:
            parser.error("prepare needs both source JSON paths; replay needs a request, two digests, witness, three pinned code helpers and epoch")
    except (AttributeError, KeyError, TypeError, ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
