# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import json
import os
import struct
import subprocess
import sys
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import convert
from convert.adapters.Fusion import MakeFusionDoc
from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import SeriesItems
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.ContainerCodec.ContainerLayout import KAssetPrefix
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Snapshots.EmitSnapPart import EmitSnapPart
from convert.Formats.Fusion.DocumentCodec.DraftDesign import DraftDesign
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.Materials.BuildMatPart import BuildMatPart
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSnap import DocumentSnap
from convert.Formats.Fusion.DocumentCodec.PackDocument import PackDocument
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.Records.EmitDesign import EmitDesign
from convert.Formats.Fusion.DocumentCodec.Rectangle.BuildPrismPart import BuildPrismPart

research = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(research / name) for name in ("SavedCuboidGeneration", "SavedCuboidSnapshot")]
from GenerateSemantic import (
    DEFAULT_WRITTEN_AT,
    check_geometry,
    check_material,
    publish,
    read_request,
    request_spec,
    require,
)
from ProbePrismSnapshot import build_snapshot, check_saved_ownership
from EncoderRoundTrip import Fusion
from SnapshotOwners import SnapshotRootPlan, stage_snapshot_owners

CHILD_MODE = "--kit-fusion-generated-snapshot-child"
LOGICAL_FILENAME = "generated-snapshot.f3d"
EXPERIMENTAL_ADDRESSES = (0, 0, 0)


def stage_parameter_observers(author):
    roles = sorted(
        (
            entity
            for entity in author.Entities
            if entity.ParentRole == "parameters" and entity.ClassName == "Parameter"
        ),
        key=lambda entity: entity.FieldValues["creationIndex"],
    )
    require(
        len(roles) == 7 and len({entity.FieldValues["creationIndex"] for entity in roles}) == 7,
        "Generated snapshot requires an ordered seven-parameter table",
    )
    helper = author.FindEntity("parameter_names")
    subjects = ["parameters", *(entity.RoleName for entity in roles)]
    require(
        len(helper.Subjects) == len(subjects) and set(helper.Subjects) == set(subjects),
        "Constructor parameter observer inventory disagrees",
    )
    helper.Subjects[:] = subjects


def emit_snapshot_document(document):
    # This alias is resolved inside the existing short-lived seed context.
    from convert.Formats.Fusion.DocumentCodec.EmitDocument import MakeUuid

    spec = Fusion._authoring_spec(document)
    author = DraftDesign(spec, str(MakeUuid()))
    initial = EmitDesign(author)
    parts = BuildPrismPart(spec, initial) + BuildMatPart(initial)
    base = ReadDocument(PackDocument(initial, spec.Title, parts))
    snapshot = build_snapshot(base)
    roots = tuple(range(snapshot.Header.RootCount - 1, 0, -1))
    require(len(roots) == 3, "Generated snapshot requires three top entity roles")
    member = stage_snapshot_owners(author, SnapshotRootPlan(*roots), addresses=EXPERIMENTAL_ADDRESSES)
    stage_parameter_observers(author)
    validated = DocumentSnap(member, snapshot)
    candidate = PackDocument(
        EmitDesign(author),
        spec.Title,
        (*parts, EmitSnapPart(validated)),
        AssetProperties=(("documentName", spec.Title),),
    )
    decoded = ReadDocument(candidate)
    require(
        decoded.Snapshots == (validated,)
        and decoded.Bodies == base.Bodies
        and decoded.Materials == base.Materials,
        "Generated snapshot changed authored body or material data during binding",
    )
    return candidate


def emit_child():
    # The shared encoder's UUID allocator and clock stay unchanged. Only its research
    # writer callback is replaced here, and only inside this dedicated subprocess.
    with patch.object(Fusion, "_write", emit_snapshot_document):
        Fusion._emit_child()


def seeded_candidate(document, written_at):
    require(type(written_at) is int and 0 <= written_at <= 253402300799, "Expected supported Unix seconds")
    request = json.dumps(
        [LOGICAL_FILENAME, written_at, document.to_json(indent=None)], allow_nan=False
    ).encode("utf-8")
    sdk = str(Path(convert.__file__).resolve().parents[1])
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(filter(None, (sdk, environment.get("PYTHONPATH"))))
    child = subprocess.run(
        [sys.executable, "-B", str(Path(__file__).resolve()), CHILD_MODE],
        input=request,
        capture_output=True,
        check=False,
        env=environment,
        timeout=60,
    )
    if child.returncode:
        lines = child.stderr.decode("utf-8", errors="replace").strip().splitlines()
        raise ValueError(f"Snapshot emitter failed: {lines[-1][:500] if lines else child.returncode}")
    output = child.stdout
    require(len(output) >= 8, "Snapshot emitter response is incomplete")
    count = struct.unpack_from("!I", output)[0]
    payload_at = 4 + 16 * count
    require(
        0 < count <= 256 and output[payload_at:].startswith(b"PK\x03\x04"),
        "Snapshot emitter response is not a native ZIP",
    )
    require(
        len({output[index : index + 16] for index in range(4, payload_at, 16)}) == count,
        "Snapshot emitter returned duplicate seeded UUIDs",
    )
    return output[payload_at:]


def build(request, *, written_at=DEFAULT_WRITTEN_AT):
    spec = request_spec(request)
    candidate = seeded_candidate(MakeFusionDoc(spec), written_at)
    model = ReadDocument(candidate)
    require(
        len(model.Snapshots) == 1 and not model.Configurations and model.Graphics is None,
        "Generated archive has an unexpected auxiliary inventory",
    )
    graph = BuildGraph(model)
    context = SelectExtrusion(graph)
    geometry = check_geometry(graph, context, model, spec)
    check_material(graph, context.BodyNode, model, spec)
    require(
        (
            context.Component.Fields["userName"],
            context.Sketch.Fields["userName"],
            context.Extrude.Fields["featureUserName"],
            context.BodyNode.Fields["userName"],
        )
        == (spec.Title, spec.SketchName, spec.ExtrusionName, spec.BodyName),
        "Generated object names disagree with the request",
    )
    snapshot = model.Snapshots[0]
    require(
        snapshot.Snapshot == build_snapshot(model), "Stored snapshot differs from the solved prism and sketch"
    )
    check_saved_ownership(model)
    serializer = graph.OneClass("BRepSerializer")
    generator = ResolveField(graph, serializer, "topEntityPIDGenerator", "PassiveIdGenerator")
    roots = SeriesItems(generator.Fields["scanOrderIndex"])
    addresses = SeriesItems(generator.Fields["addressOfTopEntities"])
    require(addresses == EXPERIMENTAL_ADDRESSES, "Generated address experiment changed its policy")
    require(ReadDocument(EmitParsed(model)) == model, "Snapshot archive lost typed state on re-emission")
    public = convert.open_document(candidate, source_format="f3d")
    require(
        set(public.metadata) == {"fusion.native_state", "fusion.read_only"}
        and public.metadata["fusion.read_only"] is True
        and CheckContract(public.metadata["fusion.native_state"], "model", Version=2) == model,
        "Strict public readback does not preserve the complete snapshot model",
    )
    require(
        len(public.configurations) == 1 and public.configurations[0].name == spec.Title,
        "Strict public snapshot title differs from the requested title",
    )
    part = EmitSnapPart(snapshot)
    archive_member = KAssetPrefix + part.Name
    with ZipFile(BytesIO(candidate)) as archive:
        archived_snapshot = archive.read(archive_member)
    require(archived_snapshot == part.Payload, "Snapshot archive member differs from the generated payload")
    return candidate, {
        "schema": 1,
        "written_at": written_at,
        "candidate_sha256": sha256(candidate).hexdigest(),
        "candidate_bytes": len(candidate),
        "semantics": request,
        "source_free_constructor": True,
        "whole_saved_source_admission": False,
        "typed_readback": True,
        "strict_public_readback": True,
        "native_acceptance": "unmeasured",
        "vendor_loadable": False,
        "application_usable": False,
        "native_checks": {**geometry, "linked_generic_material": True},
        "snapshot": {
            "member": part.Name,
            "archive_member": archive_member,
            "sha256": sha256(archived_snapshot).hexdigest(),
            "bytes": len(archived_snapshot),
            "root_ids": dict(zip(("tool_solid", "profile_region", "sketch_sheet"), roots, strict=True)),
            "addresses": list(addresses),
            "address_policy": "experimental_zero_values_native_unmeasured",
        },
        "unsupported_semantics": [
            "native_saved_display_state",
            "native_saved_configuration_parts",
            "native_saved_previews",
            "procedural_material_mapping",
            "preserved_source_graph",
        ],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate a source-free Fusion fixed-corner cuboid with an experimental snapshot"
    )
    parser.add_argument("request", type=Path, help="version 1 semantic JSON input")
    parser.add_argument("output", type=Path, help="new .f3d destination")
    parser.add_argument("--written-at", type=int, default=DEFAULT_WRITTEN_AT)
    args = parser.parse_args()
    try:
        require(args.output.suffix.lower() == ".f3d", "Output path must end in .f3d")
        require(
            not args.output.exists() and not args.output.is_symlink(), "Output destination already exists"
        )
        request, request_hash = read_request(args.request)
        payload, report = build(request, written_at=args.written_at)
        receipt = (
            json.dumps({**report, "request_sha256": request_hash}, sort_keys=True, allow_nan=False) + "\n"
        ).encode("utf-8")
        publish(args.output, payload)
        sys.stdout.buffer.write(receipt)
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        OverflowError,
        RuntimeError,
        subprocess.TimeoutExpired,
    ) as error:
        parser.exit(1, f"Fusion snapshot generation refused: {error}\n")


if __name__ == "__main__":
    if sys.argv[1:] == [CHILD_MODE]:
        emit_child()
    else:
        main()
