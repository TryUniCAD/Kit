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
from convert.Formats.Fusion.ContainerCodec.ContainerLayout import KAssetPrefix
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.MaterialCodec.Package.EmitPackage import EmitPackage
from interchange import CadDocument

from PlacementDesign import projection, read_placement, stage_placement
from PlacementRequest import Appearance, OPEN_SCOPE, SCHEMA, origin_bits, require, validate
from GenerateSemantic import DEFAULT_WRITTEN_AT, publish, read_request
from DistinctMaterialAppearances import GenerateSavedCuboid as Distinct

CHILD_MODE = "--kit-fusion-design-texture-child"


def emit_child():
    request, written_at = json.load(sys.stdin)
    appearance, origin = validate(request)
    bindings = Distinct.Materials.Configuration.Cameras.Parameters
    native_encoder = bindings.Snapshot.Fusion
    old_stage, old_seed = bindings.stage_bindings, native_encoder._emit_child
    identity = sha256(origin_bits(origin)).hexdigest()

    def stage(author, cuboid):
        return stage_placement(old_stage(author, cuboid), origin)

    def seed():
        basename, moment, document = json.load(sys.stdin)
        scoped_name = basename.removesuffix(".f3d") + f"-design-texture-placement-{identity}.f3d"
        with patch.object(sys, "stdin", io.StringIO(json.dumps([scoped_name, moment, document]))):
            old_seed()

    # These process-local research callbacks extend the prior typed emitter using only this request.
    with (
        patch.object(bindings, "stage_bindings", stage),
        patch.object(native_encoder, "_emit_child", seed),
        patch.object(sys, "stdin", io.StringIO(json.dumps([appearance, written_at]))),
    ):
        Distinct.emit_child()


def seeded_candidate(request, written_at):
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
        raise ValueError(f"Design texture emitter failed: {errors[-1][:500] if errors else child.returncode}")
    output = child.stdout
    require(len(output) >= 8, "Design texture emitter response is incomplete")
    count = struct.unpack_from("!I", output)[0]
    payload_at = 4 + 16 * count
    candidate = output[payload_at:]
    require(
        0 < count <= 256
        and candidate.startswith(b"PK\x03\x04")
        and len({output[index : index + 16] for index in range(4, payload_at, 16)}) == count,
        "Design texture emitter response does not frame a uniquely identified ZIP",
    )
    return candidate


def build(request, *, written_at=DEFAULT_WRITTEN_AT):
    appearance, origin = validate(request)
    wanted = origin_bits(origin)
    candidate = seeded_candidate(request, written_at)
    config = Appearance.Material.Config
    cameras = config.Cameras
    model, document = cameras.open_saved(candidate)
    observed = projection(model, document)
    camera_request = appearance["material_request"]["configuration_request"]["camera_request"]
    views = cameras.canonical_views(camera_request["named_views"])
    physical = Appearance.validate(appearance)
    require(
        observed == request
        and origin_bits(observed["wood_origin_cm"]) == wanted
        and Appearance.fingerprint(*Appearance.validate(observed["appearance_request"])[1:])
        == Appearance.fingerprint(*physical[1:]),
        "Generated Design texture placement or distinct material differs from the request",
    )
    snapshot = Distinct.check_snapshot(model)
    reread = ReadDocument(EmitParsed(model))
    durable = CadDocument.from_json(document.to_json())
    state = CheckContract(durable.metadata["fusion.native_state"], "model", Version=2)
    require(
        durable == document
        and reread == state == model
        and all(origin_bits(read_placement(value)[0]) == wanted for value in (reread, state))
        and all(
            cameras.canonical_views(cameras.named_views(value)) == views for value in (model, reread, state)
        ),
        "Generated Design texture placement changed through typed re-emission or strict public JSON",
    )
    part = model.Materials[0]
    material_member, snapshot_member = KAssetPrefix + part.Name, KAssetPrefix + snapshot.Name
    with ZipFile(io.BytesIO(candidate)) as archive:
        members = config.part_receipts(model, archive)
        protein, stored_snapshot = archive.read(material_member), archive.read(snapshot_member)
    require(protein == EmitPackage(part.Package), "Archive material differs from the typed package")
    require(stored_snapshot == snapshot.Payload, "Actual archive snapshot differs from generated payload")
    return candidate, {
        "schema": SCHEMA,
        "research_only": True,
        "whole_saved_source_admission": False,
        "native_acceptance": "unmeasured",
        "vendor_loadable": False,
        "application_usable": False,
        "strict_public_readback": True,
        "typed_readback": True,
        "semantic_distinct_appearances_equal": True,
        "design_texture_placement_equal": True,
        "wood_origin_cm": observed["wood_origin_cm"],
        "wood_origin_bits": wanted.hex(),
        "mapping_bounds": "inverted_finite_empty_box",
        "graphics_scene_present": False,
        "candidate_sha256": sha256(candidate).hexdigest(),
        "candidate_bytes": len(candidate),
        "written_at": written_at,
        "material_member": {"archive_member": material_member, "sha256": sha256(protein).hexdigest()},
        "configuration_members": members,
        "named_view_count": len(camera_request["named_views"]),
        "named_views_sha256": sha256(views).hexdigest(),
        "snapshot": {"archive_member": snapshot_member, "sha256": sha256(stored_snapshot).hexdigest()},
        "open_saved_scope": OPEN_SCOPE,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate a research cuboid with independently authored Design texture placement"
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
        parser.exit(1, f"Design texture placement generation refused: {error}\n")


if __name__ == "__main__":
    if sys.argv[1:] == [CHILD_MODE]:
        emit_child()
    else:
        main()
