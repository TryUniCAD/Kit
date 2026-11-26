# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import io
import json
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from struct import unpack_from
from subprocess import check_output
from tempfile import TemporaryDirectory
import sys
from types import SimpleNamespace
from unittest.mock import patch

import convert
from ApplicationWorkers.ApplicationProtocol import exclusive_rename, sync_directory, write_new
from PairedCaptureIntake import require, sha256
from P03CandidateRequest import canonical_json
from ProbeBossAuthor import DRIVERS, generate_boss
from SourceBossProbe import PROGRAMS, candidate_evidence, new_output, read_pinned_cases, source_geometry
from SourceBossRequest import prepare_request, read_replay_input
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion

SEED_REVISION = "a0c6e9f22082c7e0937f02af4464a1c06df9ed65"
SEED_SOURCE = "re/automation/EncoderRoundTrip/Fusion.py"
SEED_BLOB = "ff451cb90c337024401d87b9536275c07f43e9c2"
SEED_SHA256 = "3cf89358a5ec58935d75135b171383f562f7b7b5defc1359594bf72c0e248826"
REPLAY_PROGRAMS = (*PROGRAMS, "SourceBossRequest.py", "SourceBossReplay.py")
ARCHIVE_NAME = "P03-baseline-a.f3d"
REPORT_NAME = "P03CandidateEvidence.json"
SDK_MODULES = (
    "convert",
    "convert.adapters.Fusion.Native.Rectangle.ReadRectDims",
    "convert.adapters.Fusion.Projection.NativeProfile",
    "convert.Formats.Fusion.DocumentCodec.ReadDocument",
    "convert.Formats.Fusion.DocumentCodec.EmitDocument",
    "convert.Formats.Fusion.DocumentCodec.Model.CreateAuthor",
    "convert.Formats.Fusion.DocumentCodec.Materials.CreateMatIds",
    "convert.Formats.Fusion.DocumentCodec.Materials.BuildMaterial",
    "convert.Formats.Fusion.DocumentCodec.Rectangle.BuildPrismPart",
    "convert.Formats.Fusion.DocumentCodec.PackDocument",
)


def sdk_origins():
    root = Path(convert.__file__).resolve().parents[1]
    result = {}
    for name in SDK_MODULES:
        path = Path(import_module(name).__file__).resolve()
        require(path.is_relative_to(root), f"P03 codec imported {name} outside the selected SDK")
        result[name] = {"path": path.relative_to(root).as_posix(), "sha256": sha256(path.read_bytes())}
    return root, result


def publish_pair(output, first, second):
    with TemporaryDirectory(prefix=".kit-p03-", dir=output.parent) as temp:
        result = Path(temp) / "result"
        result.mkdir()
        for name, data in (first, second):
            write_new(result / name, data)
        exclusive_rename(result, output)
        sync_directory(output.parent)


def prepare_output(output, source_path, logical_path):
    output = new_output(output)
    source_json, logical_json = source_path.read_bytes(), logical_path.read_bytes()
    payload, witness = prepare_request(source_json, logical_json)
    snapshot, report_pin, reopened, tolerances, cases = read_pinned_cases()
    (case,) = [entry for entry in cases if entry["variant"] == witness["variant"]]
    sizes, edges, source_name, feature_id = source_geometry(snapshot, case)
    require(
        case["source"]["sha256"] == witness["source_archive_sha256"]
        and dict(zip(DRIVERS, sizes, strict=True)) == witness["dimensions_mm"]
        and source_name == witness["names"]["body"],
        "P03 reopened source differs from the prepared source witness",
    )
    observed = reopened[Path(case["source"]["path"]).name]
    witness["capture"] = {
        "receipt": report_pin,
        "case": case,
        "perimeter_world_mm": edges,
        "feature_id": feature_id,
        "tolerances": tolerances,
        "measurements": {
            key: observed[key]
            for key in ("body_count", "center_of_mass_mm", "volume_mm3")
        },
    }
    sdk_root, sdk_modules = sdk_origins()
    require(sdk_root == snapshot.root / "src", "P03 preparation requires the trusted checkout's SDK")
    witness["sdk"] = {
        "revision": check_output(["git", "rev-parse", "HEAD"], cwd=snapshot.root, text=True).strip(),
        "modules": sdk_modules,
    }
    encoded = canonical_json(witness)
    require(
        (source_path.read_bytes(), logical_path.read_bytes()) == (source_json, logical_json),
        "P03 input changed during replay preparation",
    )
    publish_pair(output, ("P03Request.json", payload), ("P03SourceWitness.json", encoded))
    return {"request_sha256": sha256(payload), "source_witness_sha256": sha256(encoded)}


def load_seed_helper(path):
    path = path.resolve(strict=True)
    source = path.read_bytes()
    require(sha256(source) == SEED_SHA256, "P03 seed helper differs from the pinned Git blob")
    spec = spec_from_file_location("_p03_fusion_seed", path)
    require(spec is not None, "P03 seed helper must be a Python source file")
    module = module_from_spec(spec)
    # Execute the checked byte sequence so a file change cannot replace the imported helper.
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


def seeded_archive(helper, witness, request_sha256, witness_sha256, written_at):
    require(type(written_at) is int and 0 <= written_at <= 253402300799, "P03 replay requires supported Unix seconds")
    dimensions = witness["dimensions_mm"]
    sizes = tuple(dimensions[key] for key in DRIVERS)
    saved_name = witness["body_label_evidence"]["saved_compatibility_label"]
    document = helper.make_cuboid("P03 replay seed", *sizes)
    logical_name = f"P03-{request_sha256}-{witness_sha256}.f3d"
    command = io.StringIO(json.dumps([logical_name, written_at, document.to_json(indent=None)], allow_nan=False))
    output = io.BytesIO()

    def emit_direct_owned(_document):
        allocator = import_module("convert.Formats.Fusion.DocumentCodec.EmitDocument")
        return generate_boss(witness["variant"], sizes, saved_name, asset_id=str(allocator.MakeUuid()))

    # This command owns the process and borrows only the existing encoder's seed context.
    with (
        patch.object(helper, "_write", emit_direct_owned),
        patch.object(sys, "stdin", command),
        patch.object(sys, "stdout", SimpleNamespace(buffer=output)),
    ):
        helper._emit_child()
    response = output.getvalue()
    require(len(response) > 4, "P03 seed helper response is incomplete")
    count = unpack_from("!I", response)[0]
    end = 4 + 16 * count
    require(
        count == 22 and len({response[i:i + 16] for i in range(4, end, 16)}) == count
        and response[end:].startswith(b"PK\x03\x04"),
        "P03 seed helper did not return 22 unique identities and a native archive",
    )
    return response[end:]


def readback_order(case, evidence):
    target_rules = evidence["target_anchor_and_dimensions"]
    result = {}
    for name, row in zip(DRIVERS[:2], target_rules["dimensions"], strict=True):
        source = tuple(tuple(point) for point in case["dimensions"][name]["source"]["operands_world_mm"])
        target = tuple(tuple(value * 10 for value in point) for point in row["cached_measurement"]["ordered_endpoints_cm"])
        preserved = name == "width_mm"
        require(
            target == (source if preserved else source[::-1]),
            f"P03 {name} has unexpected ordered source and target endpoints",
        )
        result[name] = {
            "source_world_mm": source,
            "target_world_mm": target,
            "status": "preserved" if preserved else "reversed_unqualified",
        }
    return result


def replay_evidence(archive, witness, context):
    capture = witness["capture"]
    case = capture["case"]
    sizes = tuple(witness["dimensions_mm"][key] for key in DRIVERS)
    require(
        case["variant"] == witness["variant"]
        and case["source"]["sha256"] == witness["source_archive_sha256"]
        and case["boss"]["source"]["operation"] == "join",
        "P03 replay capture differs from the prepared source witness",
    )
    evidence = candidate_evidence(
        case, archive, sizes, capture["perimeter_world_mm"], capture["measurements"], capture["tolerances"]
    )
    model = ReadDocument(archive)
    body = SelectExtrusion(BuildGraph(model)).BodyNode
    body_name = body.Fields["userName"]
    require(
        body_name == witness["body_label_evidence"]["saved_compatibility_label"]
        and evidence["target_body"]["operation"] == "new_body",
        "P03 generated body name or operation differs from its target intent",
    )
    try:
        convert.open_document(archive, source_format="f3d", strict=True)
    except ValueError as exc:
        public_read = {"status": "refused", "diagnostic": str(exc)}
    else:
        public_read = {"status": "returned_document"}
    return {
        "scope": "source-absent deterministic P03 Fusion Boss research replay",
        "qualification": "candidate_requires_licensed_target_acceptance",
        "source_operation": "join",
        "target_operation": "create",
        "source_witness": witness,
        "target_body_name": body_name,
        "operand_order": readback_order(case, evidence),
        "public_strict_read": public_read,
        "vendor_loadable": False,
        "application_usable": False,
        "whole_source_admission": False,
        "candidates": [{"file": ARCHIVE_NAME, **evidence}],
        **context,
    }


def replay_output(output, request, request_sha256, source_witness, witness_sha256, seed_helper, written_at):
    output = new_output(output)
    payload = request.read_bytes()
    witness_bytes = source_witness.read_bytes()
    witness = json.loads(witness_bytes)
    require(
        sha256(witness_bytes) == witness_sha256 and canonical_json(witness) == witness_bytes,
        "P03 source witness does not match the independently retained digest",
    )
    read_replay_input(payload, request_sha256, witness)
    sdk_root, sdk_modules = sdk_origins()
    require(sdk_modules == witness["sdk"]["modules"], "P03 replay SDK differs from the prepared codec fingerprints")
    helper = load_seed_helper(seed_helper)
    archive = seeded_archive(helper, witness, request_sha256, witness_sha256, written_at)
    result = replay_evidence(archive, witness, {
        "request_sha256": request_sha256,
        "source_witness_sha256": witness_sha256,
        "written_at": written_at,
        "generator_sources": {
            name: sha256(Path(__file__).with_name(name).read_bytes())
            for name in REPLAY_PROGRAMS
        },
        "seed_helper": {
            "path": SEED_SOURCE, "revision": SEED_REVISION,
            "git_blob": SEED_BLOB, "sha256": SEED_SHA256,
            "import_origin": str(Path(helper.__file__).resolve()),
        },
        "sdk": {
            "import_origin": str(sdk_root),
            **witness["sdk"],
        },
    })
    require(
        (request.read_bytes(), source_witness.read_bytes()) == (payload, witness_bytes),
        "P03 replay input changed during generation",
    )
    encoded = canonical_json(result)
    publish_pair(output, (ARCHIVE_NAME, archive), (REPORT_NAME, encoded))
    return {"candidate_sha256": sha256(archive), "report_sha256": sha256(encoded)}
