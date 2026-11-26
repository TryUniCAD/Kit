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
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Snapshots.EmitSnapPart import EmitSnapPart
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange import CadDocument

from CameraRequest import (
    OPEN_SCOPE,
    SCHEMA,
    camera_fields,
    canonical_views,
    named_views,
    open_saved,
    projection,
    require,
    validate,
    validate_cuboid,
)
from GenerateSemantic import DEFAULT_WRITTEN_AT, check_material, publish, read_request
from SavedParameterBindings import GenerateSavedCuboid as Parameters

CHILD_MODE = "--kit-fusion-saved-camera-child"


def stage_named_views(author, views):
    container = author.FindEntity("named_views")
    require(
        container.ClassName == "NamedViews"
        and container.ParentRole is None
        and author.FindEntity("settings").FieldValues["namedViews"] == author.Reference("named_views")
        and not any(entity.ClassName in {"Camera", "NamedView"} for entity in author.Entities),
        "Fresh constructor named-view owner is unavailable",
    )
    for index, view in enumerate(views):
        camera = f"named_camera_{index}"
        author.Allocate(camera, "Camera", Fields=camera_fields(view["camera"]))
        author.Allocate(
            f"named_view_{index}",
            "NamedView",
            ParentRole="named_views",
            Fields={
                "m_name": view["name"],
                "m_bEnableModify": view["allow_modify"],
                "m_rCamera": author.Reference(camera),
            },
        )
    return author


def emit_child():
    request, written_at = json.load(sys.stdin)
    request = validate(request)
    views = request["named_views"]
    views_seed = sha256(canonical_views(views)).hexdigest()
    old_stage, old_emit = Parameters.stage_bindings, Parameters.Snapshot.Fusion._emit_child

    def stage(author, cuboid):
        return stage_named_views(old_stage(author, cuboid), views)

    def seed_named_views():
        basename, moment, document = json.load(sys.stdin)
        seed_input = io.StringIO(
            json.dumps([basename.removesuffix(".f3d") + f"-{views_seed}.f3d", moment, document])
        )
        with patch.object(sys, "stdin", seed_input):
            old_emit()

    # Only the research drafts and deterministic seed input in this isolated child are extended.
    with patch.object(Parameters, "stage_bindings", stage), patch.object(
        Parameters.Snapshot.Fusion, "_emit_child", seed_named_views
    ), patch.object(sys, "stdin", io.StringIO(json.dumps([request["cuboid"], written_at]))):
        Parameters.emit_child()


def seeded_candidate(request, written_at):
    require(type(written_at) is int and 0 <= written_at <= 253402300799, "Expected supported Unix seconds")
    payload = json.dumps([request, written_at], allow_nan=False).encode("utf-8")
    environment = os.environ.copy()
    sdk = str(Path(convert.__file__).resolve().parents[1])
    environment["PYTHONPATH"] = os.pathsep.join(filter(None, (sdk, environment.get("PYTHONPATH"))))
    child = subprocess.run(
        [sys.executable, "-B", str(Path(__file__).resolve()), CHILD_MODE],
        input=payload,
        capture_output=True,
        check=False,
        env=environment,
        timeout=60,
    )
    if child.returncode:
        errors = child.stderr.decode("utf-8", errors="replace").strip().splitlines()
        raise ValueError(f"Named-camera emitter failed: {errors[-1][:500] if errors else child.returncode}")
    output = child.stdout
    require(len(output) >= 8, "Named-camera emitter response is incomplete")
    count = struct.unpack_from("!I", output)[0]
    payload_at = 4 + 16 * count
    candidate = output[payload_at:]
    require(
        0 < count <= 256
        and candidate.startswith(b"PK\x03\x04")
        and len({output[index : index + 16] for index in range(4, payload_at, 16)}) == count,
        "Named-camera emitter response does not frame a uniquely identified ZIP",
    )
    return candidate


def build(request, *, written_at=DEFAULT_WRITTEN_AT):
    request = validate(request)
    candidate = seeded_candidate(request, written_at)
    model, document = open_saved(candidate)
    observed = projection(model, document)
    encoded_views = canonical_views(request["named_views"])
    require(
        observed["cuboid"] == request["cuboid"] and canonical_views(observed["named_views"]) == encoded_views,
        "Strict generated parameter or named-camera field differs from semantic request",
    )
    require(
        model.Graphics is None
        and not model.Configurations
        and len(model.Snapshots) == len(model.Bodies) == 1,
        "Unexpected generated auxiliary data",
    )
    graph = BuildGraph(model)
    context = SelectExtrusion(graph)
    check_material(graph, context.BodyNode, model, validate_cuboid(request["cuboid"]))
    (snapshot,) = model.Snapshots
    require(
        snapshot.Snapshot == Parameters.Snapshot.build_snapshot(model),
        "Stored snapshot differs from the solved prism and sketch",
    )
    Parameters.Snapshot.check_saved_ownership(model)
    serializer = graph.OneClass("BRepSerializer")
    owner = ResolveField(graph, serializer, "topEntityPIDGenerator", "PassiveIdGenerator")
    require(
        SeriesItems(owner.Fields["addressOfTopEntities"]) == Parameters.Snapshot.EXPERIMENTAL_ADDRESSES,
        "Generated snapshot address policy changed",
    )
    reread = ReadDocument(EmitParsed(model))
    require(
        reread == model and canonical_views(named_views(reread)) == encoded_views,
        "Named-camera archive loses typed state on re-emission",
    )
    reloaded = CadDocument.from_json(document.to_json())
    require(
        reloaded == document
        and canonical_views(
            named_views(CheckContract(reloaded.metadata["fusion.native_state"], "model", Version=2))
        )
        == encoded_views,
        "Generated strict document loses named-camera state through JSON",
    )
    part = EmitSnapPart(snapshot)
    path = KAssetPrefix + part.Name
    with ZipFile(io.BytesIO(candidate)) as archive:
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
        "semantic_named_views_equal": True,
        "semantic_bindings_equal": True,
        "candidate_sha256": sha256(candidate).hexdigest(),
        "candidate_bytes": len(candidate),
        "written_at": written_at,
        "named_view_count": len(observed["named_views"]),
        "named_views_sha256": sha256(encoded_views).hexdigest(),
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
        description="Generate a research cuboid from explicit parameter and named-camera semantics"
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
        parser.exit(1, f"Saved cuboid named-camera generation refused: {error}\n")


if __name__ == "__main__":
    if sys.argv[1:] == [CHILD_MODE]:
        emit_child()
    else:
        main()
