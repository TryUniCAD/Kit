# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import io
import json
import os
import struct
import subprocess
import sys
from hashlib import sha256
from importlib import import_module
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import convert
from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import SeriesItems
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.ContainerCodec.ContainerLayout import KAssetPrefix
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Configuration.EmitConfigPart import EmitConfigPart
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Snapshots.EmitSnapPart import EmitSnapPart
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange import CadDocument

from ConfigRequest import (
    OPEN_SCOPE,
    SCHEMA,
    configuration_order,
    part_receipts,
    projection,
    require,
    stage_configurations,
    unify_trigger_records,
    validate,
)
from GenerateSemantic import DEFAULT_WRITTEN_AT, check_material, publish, read_request
from SavedCameras import GenerateSavedCuboid as Cameras

CHILD_MODE = "--kit-fusion-saved-config-child"


def emit_child():
    request, written_at = json.load(sys.stdin)
    request = validate(request)
    order = request["configuration_parts"]
    require(bool(order), "Configured emitter requires the explicit empty pair")
    snapshot = Cameras.Parameters.Snapshot
    old_draft, old_pack, old_seed = snapshot.DraftDesign, snapshot.PackDocument, snapshot.Fusion._emit_child
    design_module = import_module("convert.Formats.Fusion.DocumentCodec.Records.EmitDesign")
    old_records = design_module.DraftRecords
    config_parts = ()

    def draft(specification, asset_id):
        nonlocal config_parts
        author = old_draft(specification, asset_id)
        config_parts = tuple(map(EmitConfigPart, stage_configurations(author, order)))
        return author

    def pack(design, title, parts, **kwargs):
        require(len(config_parts) == 2, "Configuration triggers were not allocated by the fresh draft")
        return old_pack(design, title, (*parts, *config_parts), **kwargs)

    def seed():
        basename, moment, document = json.load(sys.stdin)
        scoped_name = basename.removesuffix(".f3d") + "-empty-config-" + "-".join(order) + ".f3d"
        with patch.object(sys, "stdin", io.StringIO(json.dumps([scoped_name, moment, document]))):
            old_seed()

    def records(author, codes):
        return unify_trigger_records(old_records(author, codes))

    # The generic class-space split leaves the part name in a continuation. The
    # two measured serializer roots keep both generated groups in the primary.
    with (
        patch.object(design_module, "DraftRecords", records),
        patch.object(snapshot, "DraftDesign", draft),
        patch.object(snapshot, "PackDocument", pack),
        patch.object(snapshot.Fusion, "_emit_child", seed),
        patch.object(sys, "stdin", io.StringIO(json.dumps([request["camera_request"], written_at]))),
    ):
        Cameras.emit_child()


def seeded_candidate(request, written_at):
    if not request["configuration_parts"]:
        return Cameras.seeded_candidate(request["camera_request"], written_at)
    require(type(written_at) is int and 0 <= written_at <= 253402300799, "Expected supported Unix seconds")
    environment = os.environ.copy()
    sdk = str(Path(convert.__file__).resolve().parents[1])
    environment["PYTHONPATH"] = os.pathsep.join(filter(None, (sdk, environment.get("PYTHONPATH"))))
    child = subprocess.run(
        [sys.executable, "-B", str(Path(__file__).resolve()), CHILD_MODE],
        input=json.dumps([request, written_at], allow_nan=False).encode(),
        capture_output=True,
        check=False,
        env=environment,
        timeout=60,
    )
    if child.returncode:
        errors = child.stderr.decode("utf-8", errors="replace").strip().splitlines()
        raise ValueError(f"Configuration emitter failed: {errors[-1][:500] if errors else child.returncode}")
    output = child.stdout
    require(len(output) >= 8, "Configuration emitter response is incomplete")
    count = struct.unpack_from("!I", output)[0]
    payload_at = 4 + 16 * count
    candidate = output[payload_at:]
    require(
        0 < count <= 256
        and candidate.startswith(b"PK\x03\x04")
        and len({output[index : index + 16] for index in range(4, payload_at, 16)}) == count,
        "Configuration emitter response does not frame a uniquely identified ZIP",
    )
    return candidate


def check_snapshot(model, spec):
    require(
        model.Graphics is None and len(model.Snapshots) == len(model.Bodies) == 1,
        "Unexpected generated auxiliary data",
    )
    graph = BuildGraph(model)
    context = SelectExtrusion(graph)
    check_material(graph, context.BodyNode, model, spec)
    (snap,) = model.Snapshots
    helpers = Cameras.Parameters.Snapshot
    require(
        snap.Snapshot == helpers.build_snapshot(model),
        "Stored snapshot differs from the solved prism and sketch",
    )
    helpers.check_saved_ownership(model)
    serializer = graph.OneClass("BRepSerializer")
    owner = ResolveField(graph, serializer, "topEntityPIDGenerator", "PassiveIdGenerator")
    require(
        SeriesItems(owner.Fields["addressOfTopEntities"]) == helpers.EXPERIMENTAL_ADDRESSES,
        "Generated snapshot address policy changed",
    )
    return EmitSnapPart(snap)


def build(request, *, written_at=DEFAULT_WRITTEN_AT):
    request = validate(request)
    candidate = seeded_candidate(request, written_at)
    model, document = Cameras.open_saved(candidate)
    views = Cameras.canonical_views(request["camera_request"]["named_views"])
    observed = projection(model, document)
    require(
        observed == request and Cameras.canonical_views(observed["camera_request"]["named_views"]) == views,
        "Strict generated camera, parameter or configuration semantics differ from the request",
    )
    part = check_snapshot(model, Cameras.validate_cuboid(request["camera_request"]["cuboid"]))
    reread = ReadDocument(EmitParsed(model))
    durable = CadDocument.from_json(document.to_json())
    state = CheckContract(durable.metadata["fusion.native_state"], "model", Version=2)
    require(
        durable == document
        and reread == state == model
        and all(configuration_order(value) == request["configuration_parts"] for value in (reread, state))
        and all(Cameras.canonical_views(Cameras.named_views(value)) == views for value in (reread, state)),
        "Empty configuration or named-camera semantics changed through the typed codec or public JSON",
    )
    path = KAssetPrefix + part.Name
    with ZipFile(io.BytesIO(candidate)) as archive:
        configuration_members = part_receipts(model, archive)
        actual = archive.read(path)
    require(actual == part.Payload, "Actual archive snapshot differs from generated payload")
    return candidate, {
        "schema": SCHEMA,
        "research_only": True,
        "whole_saved_source_admission": False,
        "native_acceptance": "unmeasured",
        "vendor_loadable": False,
        "application_usable": False,
        "strict_public_readback": True,
        "typed_readback": True,
        "semantic_bindings_equal": True,
        "semantic_named_views_equal": True,
        "semantic_configuration_envelope_equal": True,
        "candidate_sha256": sha256(candidate).hexdigest(),
        "candidate_bytes": len(candidate),
        "written_at": written_at,
        "configuration_parts": request["configuration_parts"],
        "configuration_members": configuration_members,
        "named_view_count": len(request["camera_request"]["named_views"]),
        "named_views_sha256": sha256(views).hexdigest(),
        "open_saved_scope": OPEN_SCOPE,
        "snapshot": {
            "member": part.Name,
            "archive_member": path,
            "sha256": sha256(actual).hexdigest(),
            "bytes": len(actual),
            "address_policy": "experimental_zero_values_native_unmeasured",
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate a research cuboid with an explicit empty configuration envelope"
    )
    parser.add_argument("request", type=Path)
    parser.add_argument("output", type=Path)
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
        parser.exit(1, f"Saved cuboid empty configuration generation refused: {error}\n")


if __name__ == "__main__":
    if sys.argv[1:] == [CHILD_MODE]:
        emit_child()
    else:
        main()
