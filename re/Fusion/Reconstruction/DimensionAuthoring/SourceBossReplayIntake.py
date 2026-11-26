"""Verify a sealed direct-owned P03 replay bundle before native plan preparation."""

from dataclasses import replace
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys

from Corpus import git
from P03CandidateRequest import canonical_json
from RectanglePairEvidence import RECEIPTS, REVISION, SPECIFICATION, SPECIFICATION_SHA256
import SourceBossPlan as contract
import SourceBossReplay as replay
from SourceBossRequest import read_replay_input
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument


EXTERNAL_ROLES = ("input", "manifest", "request", "witness")
HELPERS = {
    "seed_helper": (replay.SEED_SOURCE, replay.SEED_BLOB, replay.SEED_SHA256),
    "snapshot_builder": (
        replay.SNAPSHOT_SOURCE,
        replay.SNAPSHOT_BLOB,
        replay.SNAPSHOT_SHA256,
    ),
    "snapshot_owners": (replay.OWNERS_SOURCE, replay.OWNERS_BLOB, replay.OWNERS_SHA256),
}


def _git(*args):
    return git(contract.REPO, *args)


def _commit(value):
    contract.require(
        isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value),
        "Expected a full P03 Git commit",
    )
    contract.require(
        _git("rev-parse", "--verify", value + "^{commit}").decode().strip() == value,
        "Expected an exact P03 Git commit",
    )
    return value


def _json(raw):
    record = json.loads(
        raw,
        object_pairs_hook=contract.unique_object,
        parse_constant=contract.reject_constant,
    )
    contract.require(
        isinstance(record, dict) and canonical_json(record) == raw,
        "P03 replay metadata must be a canonical JSON object",
    )
    return record


def _read_inputs(paths, digests):
    contract.require(
        set(paths) == set(contract.REPLAY_FILES)
        and set(digests) == set(EXTERNAL_ROLES),
        "P03 replay input roles or independent digest roles differ",
    )
    payloads = {}
    for role, name in contract.REPLAY_FILES.items():
        path = paths[role]
        contract.require(
            path.suffix == ".py" if role in HELPERS else path.name == name,
            f"Unexpected P03 replay {role} filename",
        )
        contract.direct_directory(path.parent)
        limit = contract.ARCHIVE_LIMIT if role == "input" else contract.METADATA_LIMIT
        raw = contract.read_file(path, limit)
        digest = digests[role] if role in EXTERNAL_ROLES else HELPERS[role][2]
        contract.require(
            contract.pin(raw)["sha256"] == contract.check_digest(digest),
            f"P03 replay {role} digest differs",
        )
        payloads[role] = raw
    return payloads


def _historical_origin(value, *, basename=None, suffix=None):
    contract.require(isinstance(value, str), "P03 replay historical origin is invalid")
    path = PureWindowsPath(value) if "\\" in value else PurePosixPath(value)
    contract.require(
        path.is_absolute()
        and ".." not in path.parts
        and not any(ord(character) < 32 for character in value)
        and (basename is None or path.name == basename)
        and (suffix is None or path.suffix == suffix),
        "P03 replay historical origin is invalid",
    )
    return value


def _helper_pin(role, raw, recorded):
    path, blob, digest = HELPERS[role]
    contract.require(
        _git("rev-parse", "--verify", f"{replay.SEED_REVISION}:{path}").decode().strip()
        == blob
        and _git("cat-file", "blob", blob) == raw,
        f"P03 replay {role} differs from its committed helper blob",
    )
    expected = {
        "path": path,
        "revision": replay.SEED_REVISION,
        "git_blob": blob,
        "sha256": digest,
        "import_origin": _historical_origin(recorded["import_origin"], suffix=".py"),
    }
    contract.require(recorded == expected, f"P03 replay {role} report custody differs")
    return expected


def _sdk(witness, recorded, revision):
    root, modules = replay.sdk_origins()
    prepared = witness["sdk"]
    producer = _commit(prepared["revision"])
    tree = _git("rev-parse", "--verify", f"{producer}:src")
    contract.require(
        root == contract.REPO / "src"
        and modules == prepared["modules"]
        and set(prepared) == {"revision", "modules"}
        and tree == _git("rev-parse", "--verify", f"{revision}:src")
        and not _git("diff", "--no-ext-diff", "--name-only", revision, "--", "src")
        and not _git("ls-files", "-z", "--others", "--exclude-standard", "--", "src"),
        "P03 replay SDK differs from its pinned producer or active checkout",
    )
    for row in modules.values():
        relative = f"src/{row['path']}"
        contract.require(
            contract.pin(_git("show", f"{producer}:{relative}"))["sha256"]
            == row["sha256"],
            f"P03 replay SDK module differs from its Git blob: {relative}",
        )
    expected = {
        "revision": producer,
        "modules": modules,
        "import_origin": _historical_origin(recorded["import_origin"], basename="src"),
    }
    contract.require(recorded == expected, "P03 replay SDK report custody differs")
    return expected, tree.decode().strip()


def _programs(producer, revision, recorded):
    expected = {}
    for name in replay.REPLAY_PROGRAMS:
        relative = contract.AUTHORING / name
        path = contract.REPO / relative
        module = sys.modules.get(Path(name).stem)
        raw = contract.read_file(path)
        contract.require(
            module is not None
            and Path(module.__file__).resolve() == path
            and _git("show", f"{producer}:{relative.as_posix()}") == raw
            and _git("show", f"{revision}:{relative.as_posix()}") == raw,
            f"P03 replay program differs from its committed source: {name}",
        )
        expected[name] = contract.pin(raw)["sha256"]
    contract.require(expected == recorded, "P03 replay program report custody differs")
    return expected


def _capture(witness):
    capture = witness["capture"]
    case = capture["case"]
    receipt_path, receipt_sha = RECEIPTS["P03"]["solidworks"]
    receipt = {"path": receipt_path, "sha256": receipt_sha}
    dimensions = witness["dimensions_mm"]
    contract.require(
        witness["capture_revision"] == REVISION
        and witness["source_specification_sha256"] == SPECIFICATION_SHA256
        and witness["source_receipt"] == capture["receipt"]["capture"] == receipt
        and case["recipe"] == "P03"
        and case["variant"] == witness["variant"] == "baseline-a"
        and case["source"]["measurement_phase"]
        == witness["source_measurement_phase"]
        == "separate_process_reopen"
        and case["source"]["sha256"] == witness["source_archive_sha256"]
        and tuple(dimensions[key] for key in replay.DRIVERS) == contract.ORIGINAL_MM
        and tuple(witness["names"][key] for key in ("sketch", "boss")) == contract.FEATURES,
        "P03 replay witness does not bind the measured baseline",
    )
    receipt_bytes = _git("show", f"{REVISION}:{receipt_path}")
    contract.require(
        contract.pin(receipt_bytes)["sha256"] == receipt_sha,
        "P03 independently retained capture receipt changed",
    )
    archived_receipt = json.loads(receipt_bytes)
    folder = PurePosixPath(receipt_path).parent
    filename = f"P03-solidworks-{witness['variant']}.SLDPRT"
    (archive_row,) = (
        row for row in archived_receipt["native_files"] if row["file"] == filename
    )
    measurement_path = (folder / archived_receipt["measurements"]).as_posix()
    measurement_sha = archived_receipt["measurement_receipt_sha256"]
    measurement_bytes = _git("show", f"{REVISION}:{measurement_path}")
    specification_bytes = _git("show", f"{REVISION}:{SPECIFICATION}")
    contract.require(
        case["source"]["path"] == (folder / filename).as_posix()
        and archive_row["sha256"] == witness["source_archive_sha256"]
        and capture["receipt"]["measurements"]
        == {"path": measurement_path, "sha256": measurement_sha}
        and contract.pin(measurement_bytes)["sha256"] == measurement_sha
        and contract.pin(specification_bytes)["sha256"] == SPECIFICATION_SHA256,
        "P03 independently retained source and measurement custody differs",
    )
    measurement = json.loads(measurement_bytes)
    source_observation = measurement["observations"]["reopened_files"][filename]
    contract.require(
        measurement["authoring_process_id"] != measurement["reopen_process_id"]
        and capture["measurements"]
        == {
            key: source_observation[key]
            for key in ("body_count", "volume_mm3", "center_of_mass_mm")
        }
        and capture["tolerances"]
        == json.loads(specification_bytes)["comparison_tolerances"],
        "P03 independently reopened baseline measurements differ",
    )


def _snapshot(archive, builder):
    decoded = ReadDocument(archive)
    (entry,) = decoded.Snapshots
    generated = builder.build_snapshot(decoded)
    generated = replace(generated, Header=replace(generated.Header, IntWidth=8))
    contract.require(
        entry.Snapshot == generated and ReadDocument(EmitParsed(decoded)) == decoded,
        "P03 replay typed snapshot or complete archive readback differs",
    )


def inspect_replay(
    paths: dict[str, Path], digests: dict[str, str], revision: str
) -> tuple[dict[str, bytes], dict]:
    revision = _commit(revision)
    payloads = _read_inputs(paths, digests)
    report = _json(payloads["manifest"])
    witness = _json(payloads["witness"])
    contract.require(
        witness == report["source_witness"]
        and report["request_sha256"] == digests["request"]
        and report["source_witness_sha256"] == digests["witness"]
        and type(report["written_at"]) is int
        and 0 <= report["written_at"] <= 253402300799,
        "P03 replay report does not bind the exact request, witness and epoch",
    )
    read_replay_input(payloads["request"], digests["request"], witness)
    _capture(witness)
    sdk, sdk_tree = _sdk(witness, report["sdk"], revision)
    programs = _programs(sdk["revision"], revision, report["generator_sources"])
    helper_pins = {
        role: _helper_pin(role, payloads[role], recorded)
        for role, recorded in (
            ("seed_helper", report["seed_helper"]),
            ("snapshot_builder", report["snapshot_helpers"]["builder"]),
            ("snapshot_owners", report["snapshot_helpers"]["owners"]),
        )
    }
    builder, _ = replay.load_pinned_helper(paths["snapshot_builder"], *HELPERS["snapshot_builder"])
    archive = payloads["input"]
    _snapshot(archive, builder)
    recalculated = replay.replay_evidence(
        archive,
        witness,
        builder,
        {
            "request_sha256": digests["request"],
            "source_witness_sha256": digests["witness"],
            "written_at": report["written_at"],
            "generator_sources": programs,
            "seed_helper": helper_pins["seed_helper"],
            "snapshot_helpers": {
                "builder": helper_pins["snapshot_builder"],
                "owners": helper_pins["snapshot_owners"],
            },
            "sdk": sdk,
        },
    )
    contract.require(
        canonical_json(recalculated) == payloads["manifest"],
        "P03 replay report differs from independently reproduced strict and typed evidence",
    )
    pins = {
        role: {"file": contract.REPLAY_FILES[role], **contract.pin(raw)}
        for role, raw in payloads.items()
    }
    return payloads, {
        "input": pins["input"],
        "manifest": pins["manifest"],
        "replay_inputs": {
            role: pin for role, pin in pins.items() if role not in ("input", "manifest")
        },
        "original_generation_revision": sdk["revision"],
        "verified_program_revision": revision,
        "source_capture_revision": witness["capture_revision"],
        "source_archive": witness["source_archive_sha256"],
        "source_receipt": witness["capture"]["receipt"],
        "sdk_src_tree": sdk_tree,
        "public_strict_read": recalculated["public_strict_read"],
        "target_snapshot": recalculated["target_snapshot"],
    }
