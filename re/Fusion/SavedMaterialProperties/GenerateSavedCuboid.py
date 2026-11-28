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
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import convert
from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.Formats.Fusion.ContainerCodec.ContainerLayout import KAssetPrefix
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.Materials.PhysicalValue import PhysicalValue
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.MaterialCodec.Package.EmitPackage import EmitPackage
from interchange import CadDocument

from MaterialRequest import Config, OPEN_SCOPE, SCHEMA, canonical_properties, require, validate
from MaterialGraph import project_material
from GenerateSemantic import DEFAULT_WRITTEN_AT, publish, read_request
from SavedConfigEnvelope import GenerateSavedCuboid as Configuration

CHILD_MODE = "--kit-fusion-saved-material-child"


def emit_child():
    request, written_at = json.load(sys.stdin)
    configuration, material, component_default = validate(request)
    cameras = Configuration.Cameras
    bindings = cameras.Parameters
    make_doc, stage_bindings = bindings.MakeFusionDoc, bindings.stage_bindings
    native_encoder = bindings.Snapshot.Fusion
    existing_seed = native_encoder._emit_child

    def full_document(spec):
        return make_doc(replace(spec, Material=material))

    def stage(author, cuboid):
        author = stage_bindings(author, cuboid)
        if component_default:
            author.Change("component", defaultPhysicalMaterial=PhysicalValue(author))
            author.Change("protein", PhysicalMaterialRefCountVector=[2])
        return author

    def seed():
        basename, moment, document = json.load(sys.stdin)
        scope = "component-default" if component_default else "body-only"
        scoped_name = basename.removesuffix(".f3d") + f"-material-{scope}.f3d"
        with patch.object(sys, "stdin", io.StringIO(json.dumps([scoped_name, moment, document]))):
            existing_seed()

    # Extend only research callbacks for this process. The ordinary constructor
    # still validates the complete DocumentSpec and emits the material package.
    emitter = Configuration if configuration["configuration_parts"] else cameras
    inner_request = configuration if configuration["configuration_parts"] else configuration["camera_request"]
    with (
        patch.object(bindings, "MakeFusionDoc", full_document),
        patch.object(bindings, "stage_bindings", stage),
        patch.object(native_encoder, "_emit_child", seed),
        patch.object(sys, "stdin", io.StringIO(json.dumps([inner_request, written_at]))),
    ):
        emitter.emit_child()


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
        raise ValueError(f"Material emitter failed: {errors[-1][:500] if errors else child.returncode}")
    output = child.stdout
    require(len(output) >= 8, "Material emitter response is incomplete")
    count = struct.unpack_from("!I", output)[0]
    payload_at = 4 + 16 * count
    candidate = output[payload_at:]
    require(
        0 < count <= 256
        and candidate.startswith(b"PK\x03\x04")
        and len({output[index : index + 16] for index in range(4, payload_at, 16)}) == count,
        "Material emitter response does not frame a uniquely identified ZIP",
    )
    return candidate


def build(request, *, written_at=DEFAULT_WRITTEN_AT):
    configuration, expected, default = validate(request)
    candidate = seeded_candidate(request, written_at)
    model, document = Config.Cameras.open_saved(candidate)
    actual, linked = project_material(model)
    properties = canonical_properties(expected, default)
    require(
        actual == expected and linked == default and canonical_properties(actual, linked) == properties,
        "Generated material cannot represent the exact requested mechanics, thermal, finish or assignment",
    )
    observed = Config.projection(model, document)
    cameras = Config.Cameras
    views = cameras.canonical_views(configuration["camera_request"]["named_views"])
    require(
        observed == configuration
        and cameras.canonical_views(observed["camera_request"]["named_views"]) == views,
        "Generated candidate changed the configuration, camera or parameter semantics",
    )
    cuboid = cameras.validate_cuboid(configuration["camera_request"]["cuboid"])
    snapshot = Configuration.check_snapshot(model, replace(cuboid, Material=expected))
    typed = ReadDocument(EmitParsed(model))
    durable = CadDocument.from_json(document.to_json())
    state = CheckContract(durable.metadata["fusion.native_state"], "model", Version=2)
    require(
        durable == document
        and typed == state == model
        and all(canonical_properties(*project_material(value)) == properties for value in (typed, state))
        and all(cameras.canonical_views(cameras.named_views(value)) == views for value in (typed, state)),
        "Generated saved profile changed through typed re-emission or strict public JSON",
    )
    part = model.Materials[0]
    material_member = KAssetPrefix + part.Name
    snapshot_member = KAssetPrefix + snapshot.Name
    with ZipFile(io.BytesIO(candidate)) as archive:
        members = Config.part_receipts(model, archive)
        protein = archive.read(material_member)
        actual_snapshot = archive.read(snapshot_member)
    require(protein == EmitPackage(part.Package), "Archive material differs from the typed package")
    require(actual_snapshot == snapshot.Payload, "Actual archive snapshot differs from generated payload")
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
        "semantic_material_properties_equal": True,
        "candidate_sha256": sha256(candidate).hexdigest(),
        "candidate_bytes": len(candidate),
        "written_at": written_at,
        "material_properties_sha256": sha256(properties).hexdigest(),
        "structural_class": actual.ClassName,
        "component_default": linked,
        "material_member": {"archive_member": material_member, "sha256": sha256(protein).hexdigest()},
        "configuration_parts": observed["configuration_parts"],
        "configuration_members": members,
        "named_view_count": len(observed["camera_request"]["named_views"]),
        "named_views_sha256": sha256(views).hexdigest(),
        "snapshot": {"archive_member": snapshot_member, "sha256": sha256(actual_snapshot).hexdigest()},
        "open_saved_scope": OPEN_SCOPE,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate a research cuboid from explicit authored material semantics"
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
        parser.exit(1, f"Saved cuboid material generation refused: {error}\n")


if __name__ == "__main__":
    if sys.argv[1:] == [CHILD_MODE]:
        emit_child()
    else:
        main()
