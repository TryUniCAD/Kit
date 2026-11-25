from pathlib import PureWindowsPath
import re

from ApplicationWorkers.ApplicationProtocol import write_new
from EncoderRoundTrip.Artifacts import (
    DOCUMENT_LIMIT,
    NATIVE_LIMIT,
    RECORD_LIMIT,
    absolute,
    canonical_json,
    digest,
    read_record,
    require_directory,
)
from EncoderRoundTrip.Pipeline import APPLICATIONS, IDENTITY_FIELDS, ROLES
from NativeAcceptance.CompareDocument import SameValues
from NativeAcceptance.Records import ReadBytes
from NativeAcceptance.VerifyBatch import CheckMeasurement


_HASH = re.compile(r"[0-9a-f]{64}")


def _sha(value):
    return isinstance(value, str) and _HASH.fullmatch(value) is not None


def _check_artifact(output, name, evidence, expected, limit):
    if not _sha(expected) or evidence.get("path") != name or evidence.get("sha256") != expected:
        raise ValueError(f"{name} does not match the round-trip manifest")
    data = ReadBytes(output / name, limit)
    if evidence.get("bytes") != len(data) or digest(data) != expected:
        raise ValueError(f"{name} bytes do not match the round-trip manifest")
    return data


def _check_neutral_source(payload, format_id, source_sha256):
    from interchange.document.Models.DocumentModel import CadDocument

    try:
        document = CadDocument.from_dict(read_record(payload))
    except (AttributeError, KeyError, OverflowError, TypeError, ValueError) as error:
        raise ValueError("round-trip neutral document is not a valid CadDocument") from error
    if document.source.format_id != format_id or document.source.sha256 != source_sha256:
        raise ValueError("round-trip neutral document source does not match the manifest")


def _load_run(output, role):
    try:
        manifest = read_record(ReadBytes(output / "manifest.json", RECORD_LIMIT))
        if type(manifest["schema"]) is not int or manifest["schema"] != 1:
            raise ValueError("unsupported round-trip manifest schema")
        identity = {field: manifest[field] for field in IDENTITY_FIELDS}
        if manifest["run_fingerprint"] != digest(canonical_json(identity)):
            raise ValueError("round-trip manifest fingerprint mismatch")
        if manifest["source"]["status"] != "decoded" or manifest[role]["status"] != "awaiting_native":
            raise ValueError(f"round-trip role {role} has no generated candidate")
        if not _sha(manifest["source_sha256"]) or manifest["source"]["sha256"] != manifest["source_sha256"]:
            raise ValueError("round-trip source hash is invalid")
        format_id, suffix, _ = APPLICATIONS[manifest["application"]]
        neutral = _check_artifact(output, "document.json", manifest["source"]["neutral"], manifest["neutral_sha256"], DOCUMENT_LIMIT)
        _check_neutral_source(neutral, format_id, manifest["source_sha256"])
        candidate = _check_artifact(output, role + suffix, manifest[role]["artifact"], manifest["candidate_sha256"][role], NATIVE_LIMIT)
        return manifest, candidate
    except (AttributeError, KeyError, TypeError) as error:
        raise ValueError("round-trip manifest has invalid records") from error


def _measurement(record, name, application):
    if (
        not isinstance(record, dict)
        or record.get("application") != application
        or type(record.get("pid")) is not int
        or record["pid"] <= 0
        or not isinstance(record.get("build"), str)
        or not record["build"].strip()
        or not _sha(record.get("source_sha256"))
        or record.get("status") not in ("measured", "failed")
    ):
        raise ValueError(f"{name} is missing native measurement identity")


def _healthy(record):
    if record.get("status") == "failed":
        return False
    if (
        not isinstance(record.get("load_errors"), list)
        or type(record.get("documents_after")) is not int
        or not isinstance(record.get("opened"), dict)
        or not isinstance(record.get("rebuilt"), dict)
        or not isinstance(record.get("edits"), list)
    ):
        raise ValueError("measured native receipt has missing records")
    try:
        for key in ("opened", "rebuilt"):
            bodies = record[key]["bodies"]
            if not isinstance(bodies, list) or any(
                type(value) not in (int, float)
                for body in bodies
                for value in (body["volume_mm3"], *body["center_mm"])
            ):
                raise ValueError("measured body volume and center must use JSON numbers")
        return bool(CheckMeasurement(record))
    except (AttributeError, KeyError, OverflowError, TypeError) as error:
        raise ValueError("measured native receipt has malformed observation records") from error


def _binding(manifest, role):
    return {
        "application": manifest["application"],
        "role": role,
        "run_fingerprint": manifest["run_fingerprint"],
        "source_sha256": manifest["source_sha256"],
        "candidate_sha256": manifest["candidate_sha256"][role],
        "sdk_revision": manifest["sdk_revision"],
    }


def _validate(receipt, manifest, role):
    expected = _binding(manifest, role)
    if type(receipt.get("schema")) is not int or receipt["schema"] != 1:
        raise ValueError("unsupported encoder round-trip receipt schema")
    for field, value in expected.items():
        if receipt.get(field) != value:
            raise ValueError(f"receipt {field} does not bind this round-trip role")
    controls = receipt.get("controls")
    if not isinstance(controls, dict) or set(controls) != {"before", "after"}:
        raise ValueError("receipt requires before and after control observations")
    before, after = controls["before"], controls["after"]
    candidate = receipt.get("candidate")
    measurements = {"control before": before, "candidate": candidate, "control after": after}
    for name, record in measurements.items():
        _measurement(record, name, expected["application"])
    if candidate["source_sha256"] != expected["candidate_sha256"]:
        raise ValueError("native observation measured different candidate bytes")
    if before["source_sha256"] != after["source_sha256"] or before["source_sha256"] == candidate["source_sha256"]:
        raise ValueError("before and after controls must measure the same independent bytes")
    if len({record["build"] for record in measurements.values()}) != 1:
        raise ValueError("candidate and both controls must report one application build")
    if len({record["pid"] for record in measurements.values()}) != len(measurements):
        raise ValueError("candidate and both controls must report distinct process IDs")
    before_healthy = _healthy(before)
    after_healthy = _healthy(after)
    controls_healthy = before_healthy and after_healthy and SameValues(before["rebuilt"], after["rebuilt"])
    candidate_healthy = _healthy(candidate)
    measurement_status = (
        "invalid_controls" if not controls_healthy
        else "observed" if candidate_healthy
        else "candidate_failed"
    )
    return {**expected, "application_build": candidate["build"], "measurement_status": measurement_status}


def _validate_solidworks_exact(envelope, manifest, role, candidate):
    if manifest["application"] != "solidworks":
        raise ValueError("the exact SOLIDWORKS SDK receipt requires a SOLIDWORKS round trip")

    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion
    from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Writing.Measured.MatchMeasCase import MatchMeasCase
    from convert.adapters.solidworks.Core.Writing.Measured.MatchPartMeas import MatchPartMeas
    from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import KPartMeasureOpt
    from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import ReadPartMeas

    written_at, receipt = ReadPartMeas(WriteOptions(values={KPartMeasureOpt: envelope}))
    manifest_epoch = manifest["written_at"]
    if type(manifest_epoch) is not int or written_at != manifest_epoch:
        raise ValueError("exact SOLIDWORKS receipt epoch does not bind this round-trip role")
    locators = manifest["native_locators"]
    locator = locators.get(role) if isinstance(locators, dict) else None
    if (
        not isinstance(locator, str)
        or not PureWindowsPath(locator).is_absolute()
        or PureWindowsPath(locator).name != role + ".SLDPRT"
    ):
        raise ValueError("round-trip SOLIDWORKS locator does not identify this role")

    archive = SldprtArchive.from_bytes(candidate, "<memory>")
    fields = ReadHeaderGraph(archive.require("Header2"), KHeaderVersion).FieldsValue
    if GetFileRef(fields.get("f38")).PathValue != locator:
        raise ValueError("candidate SOLIDWORKS header locator differs from the round-trip role")
    if type(fields.get("f70")) is not int or fields["f70"] != written_at:
        raise ValueError("candidate SOLIDWORKS header epoch differs from the exact receipt")

    binding = _binding(manifest, role)
    try:
        evidence = dict(MatchPartMeas(receipt, candidate)[KPartMeasureOpt])
    except OverflowError as error:
        raise ValueError("exact SOLIDWORKS receipt contains an oversized numeric observation") from error
    case = MatchMeasCase(receipt, binding["candidate_sha256"], len(candidate))
    return {
        **binding,
        "application_build": evidence["oracle_build"],
        "measurement_status": "exact_sdk_candidate_bound",
        "receipt_kind": "solidworks_exact_sdk",
        "sdk_publication": {
            "receipt_option": KPartMeasureOpt,
            "native_locator": locator,
            "written_at": written_at,
            "oracle_case": case,
            **evidence,
        },
    }


def attach_receipt(output, role, receipt):
    if role not in ROLES:
        raise ValueError("unknown round-trip candidate role")
    output = absolute(output)
    require_directory(output)
    manifest, candidate = _load_run(output, role)
    content = ReadBytes(absolute(receipt), RECORD_LIMIT)
    record = read_record(content)
    if "schema" not in record and {"written_at", "receipt"} & record.keys():
        evidence = _validate_solidworks_exact(record, manifest, role, candidate)
    else:
        evidence = _validate(record, manifest, role)
    destination = output / (role + "-receipt.json")
    try:
        write_new(destination, content)
    except FileExistsError:
        if ReadBytes(destination, RECORD_LIMIT) != content:
            raise ValueError(f"{role} already has a different immutable receipt") from None
    return {
        **evidence,
        "receipt": {"path": destination.name, "sha256": digest(content), "bytes": len(content)},
        "status": "receipt_attached",
        "native_qualification": "pending",
        "vendor_loadable": False,
        "application_usable": False,
    }
