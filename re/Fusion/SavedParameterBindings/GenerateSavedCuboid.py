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
import math
import os
import struct
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import convert
from convert.adapters.Fusion import MakeFusionDoc
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import SeriesItems
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.ContainerCodec.ContainerLayout import KAssetPrefix
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Snapshots.EmitSnapPart import EmitSnapPart
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange import CadDocument

from BindingRequest import OPEN_SCOPE, extract, require, validate
from GenerateSemantic import DEFAULT_WRITTEN_AT, check_material, publish, read_request
from PrepareRequest import open_saved

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "GeneratedSnapshot"))
import GenerateSnapshot as Snapshot

CHILD_MODE = "--kit-fusion-saved-parameter-child"
DRAFT_PARAMETERS = {
    "width_driver": "width_user",
    "depth_driver": "depth_user",
    "height_driver": "length_parameter",
    "width": "width_model",
    "depth": "depth_model",
    "height": "along_parameter",
    "taper": "taper_parameter",
}
DRAFT_BINDINGS = {
    "width": "width_binding",
    "depth": "depth_binding",
    "height": "along_binding",
    "taper": "taper_binding",
}


def stage_bindings(author, request):
    roles = [
        entity.RoleName
        for entity in author.Entities
        if entity.ClassName == "Parameter" and entity.ParentRole == "parameters"
    ]
    require(
        len(roles) == len(DRAFT_PARAMETERS) and set(roles) == set(DRAFT_PARAMETERS.values()),
        "Fresh constructor parameter roles changed",
    )
    order = request["parameter_order"]
    names = request["parameters"]
    helper = author.FindEntity("parameter_names")
    refs = []
    observers = ["parameters"]
    for index, role in enumerate(order):
        name = DRAFT_PARAMETERS[role]
        row = names[role]
        author.Change(
            name,
            creationIndex=index + 1,
            userName=row["user_name"],
            name=row["display_name"],
            unit=row["unit"],
            expression=row["expression"],
            value=float(row["value"]),
            comment=row["comment"],
        )
        refs.append({"key": row["user_name"], "value": author.Reference(name)})
        observers.append(name)
        if role in DRAFT_BINDINGS:
            author.Change(DRAFT_BINDINGS[role], value=float(row["value"]))
    author.Change("parameters", children=[entry["value"] for entry in refs])
    author.Change("parameter_names", parameterMap=refs)
    helper.Subjects[:] = observers
    return author


def emit_child():
    request, written_at = json.load(sys.stdin)
    spec = validate(request)
    document = MakeFusionDoc(spec)
    seed = sha256(
        json.dumps(request, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    framed = io.StringIO(json.dumps([f"saved-cuboid-{seed}.f3d", written_at, document.to_json(indent=None)]))
    create_design, pack = Snapshot.DraftDesign, Snapshot.PackDocument

    def draft(specification, asset_id):
        return stage_bindings(create_design(specification, asset_id), request)

    def pack_with_title(*args, **kwargs):
        if "AssetProperties" in kwargs:
            kwargs["AssetProperties"] = (("documentName", request["title"]),)
        return pack(*args, **kwargs)

    # These aliases belong to the imported research emitter in this one child.
    # The normal SDK writer and the frozen input schema never use these callbacks.
    with patch.object(Snapshot, "DraftDesign", draft), patch.object(
        Snapshot, "PackDocument", pack_with_title
    ), patch.object(Snapshot.Fusion, "_write", Snapshot.emit_snapshot_document), patch.object(
        sys, "stdin", framed
    ):
        Snapshot.Fusion._emit_child()


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
        raise ValueError(f"Saved binding emitter failed: {errors[-1][:500] if errors else child.returncode}")
    output = child.stdout
    require(len(output) >= 8, "Saved binding emitter response is incomplete")
    count = struct.unpack_from("!I", output)[0]
    payload_at = 4 + 16 * count
    candidate = output[payload_at:]
    require(
        0 < count <= 256
        and candidate.startswith(b"PK\x03\x04")
        and len({output[i : i + 16] for i in range(4, payload_at, 16)}) == count,
        "Saved binding emitter response does not frame a uniquely identified ZIP",
    )
    return candidate


def build(request, *, written_at=DEFAULT_WRITTEN_AT):
    spec = validate(request)
    candidate = seeded_candidate(request, written_at)
    model, document = open_saved(candidate)
    observed = extract(model, document)
    require(observed == request, "Strict generated semantic parameter projection differs from the request")
    require(
        model.Graphics is None
        and not model.Configurations
        and len(model.Snapshots) == len(model.Bodies) == 1,
        "Unexpected generated auxiliary data",
    )
    graph = BuildGraph(model)
    context = SelectExtrusion(graph)
    check_material(graph, context.BodyNode, model, spec)
    snapshot = model.Snapshots[0]
    require(
        snapshot.Snapshot == Snapshot.build_snapshot(model),
        "Stored snapshot differs from the solved prism and sketch",
    )
    Snapshot.check_saved_ownership(model)
    serializer = graph.OneClass("BRepSerializer")
    owner = ResolveField(graph, serializer, "topEntityPIDGenerator", "PassiveIdGenerator")
    require(
        SeriesItems(owner.Fields["addressOfTopEntities"]) == Snapshot.EXPERIMENTAL_ADDRESSES,
        "Generated snapshot address policy changed",
    )
    require(ReadDocument(EmitParsed(model)) == model, "Generated typed state changed on codec re-emission")
    require(
        CadDocument.from_json(document.to_json()) == document,
        "Generated strict document loses state through JSON",
    )
    body = document.bodies[0].topology
    sizes = (spec.WidthMm, spec.DepthMm, spec.LengthMm)
    volume = math.prod(sizes)
    bounds = body.bounding_box
    require(
        (body.solid_count, body.shell_count, body.face_count, body.edge_count, body.vertex_count)
        == (1, 1, 6, 12, 8)
        and body.valid is True
        and bounds is not None
        and (bounds.minimum.x, bounds.minimum.y, bounds.minimum.z) == (0.0, 0.0, 0.0)
        and all(
            math.isclose(point, size, rel_tol=1e-12, abs_tol=0.0)
            for point, size in zip((bounds.maximum.x, bounds.maximum.y, bounds.maximum.z), sizes, strict=True)
        )
        and math.isclose(body.volume, volume, rel_tol=1e-12, abs_tol=0.0),
        "Generated geometry does not match the analytic cuboid",
    )
    part = EmitSnapPart(snapshot)
    with ZipFile(io.BytesIO(candidate)) as archive:
        actual = archive.read(KAssetPrefix + part.Name)
    require(actual == part.Payload, "Actual archive snapshot differs from generated payload")
    return candidate, {
        "schema": 1,
        "research_only": True,
        "whole_saved_source_admission": False,
        "native_acceptance": "unmeasured",
        "vendor_loadable": False,
        "application_usable": False,
        "strict_public_readback": True,
        "typed_readback": True,
        "semantic_bindings_equal": True,
        "candidate_sha256": sha256(candidate).hexdigest(),
        "candidate_bytes": len(candidate),
        "written_at": written_at,
        "parameter_order": request["parameter_order"],
        "analytic_volume_mm3": volume,
        "retained_material": "label_density_rgba_only",
        "snapshot": {
            "member": part.Name,
            "archive_member": KAssetPrefix + part.Name,
            "sha256": sha256(actual).hexdigest(),
            "bytes": len(actual),
            "address_policy": "experimental_zero_values_native_unmeasured",
        },
        "open_saved_scope": OPEN_SCOPE,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate a research cuboid from explicit saved parameter semantics"
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
        parser.exit(1, f"Saved cuboid generation refused: {error}\n")


if __name__ == "__main__":
    if sys.argv[1:] == [CHILD_MODE]:
        emit_child()
    else:
        main()
