import json
from math import isclose
from pathlib import Path
import re
from traceback import print_exc
from unittest.mock import patch

from AuthorImportedBody import box_expectation
from AuthorRectangleAnchors import control
from ObserveKernelBodyRestore import measure_body
from ObserveLocalImportedPart import phase
from ProjectDisclosedImport import OMISSIONS, decode_import, project_import, rectangular_boundary, source_owners
from RunImportedBodySources import oracle_identity
from RunSealedPublicBox import (
    CONTROL, LOCK_SHA, ORACLE, RAW_LOCK_SHA, SCHEMA, SLOTS, SOURCE_ROOT, VERSION,
    checked, digest, publish, require,
)
from VerifyBareImportPackage import fingerprint, guard_build
from VerifyPublicCyl import CAPS, EMITTER, FORMAT, check_target, guarded_prepare, warm

from convert import open_document, write_document
from convert.Geometry.Parasolid import KLengthScale
from convert.adapters.base.TransferContract import TransferMode
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeader
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import KMillimetersPerMeter
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KLocalBodyStream
from convert.adapters.solidworks.Core.Preparation.Imports.PlanImportPart import PlanImportPart
from interchange import CadDocument, CadSource, Configuration


FEATURE = "Imported geometry"
POSITION_M = 1e-10
MASS_TOLERANCES = {"volume_m3": 1e-22, "area_m2": 1e-18}
SOURCE_OMISSIONS = (*OMISSIONS, "source import feature name and persistent identity")


def source_path(slot):
    return Path(SOURCE_ROOT) / slot / "Source.SLDPRT"


def original_sha(lock, slot):
    return lock["sources"][slot]["source_sha256"]


def locked_specs(lock):
    location = Path(SOURCE_ROOT) / "SourceSpecifications.json"
    cases = json.loads(checked(location, lock["specifications_sha256"]))
    require(set(cases) == set(SLOTS), "independent author specification slots differ")
    return cases


def check_originals(lock):
    locked_specs(lock)
    for slot in SLOTS:
        checked(source_path(slot), original_sha(lock, slot))


def project_source(slot, lock):
    original = decode_import(checked(source_path(slot), original_sha(lock, slot)))
    projection = project_import(original)
    document = CadDocument(CadSource("kit.neutral", "", ""),
                           (Configuration("active", projection.configuration_name, True),),
                           (), (), (), (), (), (), brep=projection.model)
    require(GetDocumentCaps(document) == CAPS and not document.validate(),
            "projection acquired data besides the solid and active configuration")
    return document, projection


def neutral_sha(document):
    return digest(document.to_json(indent=None).encode("utf-8"))


def candidate_path(root, slot):
    return root / "Candidate" / slot / (slot + ".SLDPRT")


def staged_write(document, target):
    with guard_build():
        PlanImportPart(document, target)
    with patch(EMITTER + ".PrepareNative", side_effect=guarded_prepare) as prepare:
        result = write_document(document, target)
    require(prepare.call_count == 1, "the normal part writer did not prepare exactly once")
    source, stage, epoch, settings = prepare.call_args.args
    require(source is document and stage.name == target.name and stage.parent != target.parent
            and stage.parent.parent == target.parent and settings.values["final_destination"] == str(target)
            and type(epoch) is int and epoch > 0,
            "the ordinary registry did not use the actual final staged locator and event")
    payload = target.read_bytes()
    check_target(target, payload)
    require(result.path == target and result.bytes_written == len(payload) and not (result.dropped or result.requirements)
            and result.native_capabilities == result.transferred_capabilities == CAPS
            and len(result.transfers) == 2 and all(item.mode is TransferMode.KNative for item in result.transfers),
            "the ordinary writer did not transfer exactly native geometry and configuration")
    archive = SldprtArchive.from_bytes(payload)
    require(archive.format_version == 4 and len(archive.records) == 12 and bool(archive.require(KLocalBodyStream)),
            "ordinary output lacks the complete native local-body archive")
    require(all(ReadHeader(archive.require(stream), 19000).SelfFile.PathValue == str(target)
                for stream in ("Header2", "Contents/Config-0-ModelHeader")),
            "native headers lost the real destination")
    return {"candidate": fingerprint(payload), "writer_epoch": epoch, "runtime_input_reads": 0,
            "native_transfers": sorted(item.value for item in CAPS), "actual_staged_write": True}


def build(root, lock, job_sha):
    warm()
    locked_specs(lock)
    rows = {}
    for slot in SLOTS:
        document, _ = project_source(slot, lock)
        identity = neutral_sha(document)
        row = staged_write(document, candidate_path(root, slot))
        require(neutral_sha(document) == identity, "staged emission changed its neutral input")
        rows[slot] = row | {"source_sha256": original_sha(lock, slot), "neutral_sha256": identity}
    check_originals(lock)
    proof = {"schema": SCHEMA + "-build.v1", "job_sha256": job_sha, "cases": rows,
             "source_lock_sha256": RAW_LOCK_SHA, "specifications_sha256": lock["specifications_sha256"],
             "native_processes_started": 0}
    identity = publish(root / "Build.json", proof)
    return {"passed": True, "build_sha256": identity, "candidates": len(rows), "native_processes_started": 0}


def readback(payload, projection, *, saved=False):
    with guard_build():
        observed = open_document(payload, source_format=FORMAT)
    feature, config, body = source_owners(observed)
    require(feature.name == body.name == FEATURE and config.name == projection.configuration_name
            and not observed.validate(), "strict SDK read lost the actual feature, body or active configuration")
    boundary = rectangular_boundary(observed.brep, body.id)
    expected = rectangular_boundary(projection.model).limits
    if saved:
        require(all(isclose(a, b, rel_tol=0, abs_tol=1e-9)
                    for left, right in zip(boundary.limits, expected, strict=True)
                    for a, b in zip(left, right, strict=True)),
                "separate native save changed the signed SDK box boundary")
    else:
        encoded = tuple(tuple((value / KMillimetersPerMeter) / KLengthScale for value in axis) for axis in expected)
        require(boundary.limits == encoded, "staged SDK read moved a signed bound beyond its wire representation")


def independent_shape(specification):
    box = box_expectation(specification)
    expected = {"corners_m": box["corners"], "edges": len(box["edges"]), "faces": len(box["faces"]),
                "com_m": box["com"], "volume_m3": box["volume"], "area_m2": box["area"]}

    def measure_shape(observer, body, values, *, temporary):
        topology, _ = observer.body_topology(body, specification, temporary=temporary)
        return measure_body(observer, body, values, temporary=temporary) | topology

    return expected, measure_shape


def compare_shape(reference, actual):
    require(all(reference[key] == actual[key] for key in (
        "vertices", "edges", "faces", "face_edge_incidence",
    )), "native physical incidence differs from the signed source box")
    fields = [(actual[key], reference[key], tolerance) for key, tolerance in MASS_TOLERANCES.items()]
    fields.extend((a, b, 1e-11) for a, b in zip(actual["com_m"], reference["com_m"], strict=True))
    require(all(isclose(a, b, rel_tol=0, abs_tol=tol)
                and (max(abs(a), abs(b)) <= tol or format(a, ".6g") == format(b, ".6g"))
                for a, b, tol in fields), "native mass properties differ at six significant figures")


def phase_receipt(result, identities):
    if result.get("oracle_identity"):
        process = oracle_identity(result["oracle_identity"])
        identities.append((process["process_id"], process["process_creation_filetime"]))
    return {"passed": bool(result["passed"]), "record_sha256": result["record_sha256"],
            "numeric_checks": result.get("numeric_checks", 0)}


def public_build_row(row, lock, slot):
    part = row["candidate"]
    transfers = sorted(item.value for item in CAPS)
    require(row["source_sha256"] == original_sha(lock, slot)
            and re.fullmatch(r"[a-f0-9]{64}", row["neutral_sha256"])
            and re.fullmatch(r"[a-f0-9]{64}", part["sha256"])
            and type(part["bytes"]) is int and part["bytes"] > 0
            and type(row["writer_epoch"]) is int and row["writer_epoch"] > 0
            and row["runtime_input_reads"] == 0 and row["actual_staged_write"] is True
            and row["native_transfers"] == transfers, "candidate lacks its guarded native publication")
    return {"source_sha256": original_sha(lock, slot), "neutral_sha256": row["neutral_sha256"],
            "candidate": {"sha256": part["sha256"], "bytes": part["bytes"]},
            "writer_epoch": row["writer_epoch"], "runtime_input_reads": 0, "actual_staged_write": True,
            "native_transfers": transfers}


def native_case(root, slot, lock, specification, build_row, row, identities):
    document, projection = project_source(slot, lock)
    source_hash = original_sha(lock, slot)
    require(build_row["source_sha256"] == source_hash and build_row["neutral_sha256"] == neutral_sha(document),
            "the publication lock differs from the current source projection")
    target = candidate_path(root, slot)
    identity = build_row["candidate"]["sha256"]
    candidate = checked(target, identity)
    require(fingerprint(candidate) == build_row["candidate"], "candidate size changed after staging")
    readback(candidate, projection)
    row["candidate_sdk_readback"] = True
    expected, shape = independent_shape(specification)
    directory = root / "Native" / slot
    directory.mkdir(parents=True)
    saved = directory / "NativeSave.SLDPRT"

    def record(label, path, checksum, name, **options):
        result = phase(directory, label, path, checksum, expected, name, measure_shape=shape, **options)
        row["phases"][label] = phase_receipt(result, identities)
        require(result["passed"], "native phase failed")
        for snapshot in (result["cold"], result["rebuilt"]):
            require(snapshot["configuration"] == projection.configuration_name
                    and snapshot["configurations"] == (projection.configuration_name,)
                    and snapshot["application_state"]["needs_rebuild"] == 0,
                    "native active configuration or rebuild state differs")
        return result

    source = record("Original", source_path(slot), source_hash, projection.feature_name)
    opened = record("Candidate", target, identity, FEATURE, save=saved)
    reopened = record("FreshReopen", saved, opened["saved_sha256"], FEATURE,
                      reference=opened["cold"]["persistent_reference"])
    require(source["read_only"] and not opened["read_only"] and reopened["read_only"]
            and tuple(opened["save"]) == (True, 0, 0), "native save or actual access mode differs")
    owner = opened["cold"]
    for state in ("cold", "rebuilt"):
        for lane in (opened, reopened):
            snapshot = lane[state]
            require(all(snapshot[key] == owner[key] for key in
                        ("feature_id", "persistent_reference", "tree_signature")),
                    "candidate's own persistent BaseBody identity or tree changed")
            compare_shape(source[state]["shape"], snapshot["shape"])
    checked(target, identity)
    checked(source_path(slot), source_hash)
    readback(checked(saved, opened["saved_sha256"]), projection, saved=True)
    row.update(saved_sha256=opened["saved_sha256"], native_saved_sdk_readback=True,
               native_geometry_and_owners_match=True, passed=True)


def measure(packet, root, job, lock, seed, job_sha, build_sha):
    proof = json.loads(checked(root / "Build.json", build_sha))
    require(proof["schema"] == SCHEMA + "-build.v1" and proof["job_sha256"] == job_sha
            and proof["source_lock_sha256"] == RAW_LOCK_SHA and proof["native_processes_started"] == 0
            and proof["specifications_sha256"] == lock["specifications_sha256"] and tuple(proof["cases"]) == SLOTS,
            "private build lock differs from the frozen evaluation")
    staged = {slot: public_build_row(proof["cases"][slot], lock, slot) for slot in SLOTS}
    warm()
    specifications = locked_specs(lock)
    directory = root / "Native"
    directory.mkdir()
    path = directory / "Control.SLDPRT"
    require(publish(path, seed) == CONTROL, "guest-local control changed")
    identities, controls, cases = [], {}, {}
    report = {"schema": SCHEMA + "-native.v1", "job_sha256": job_sha, "build_sha256": build_sha,
              "source_receipt_sha256": LOCK_SHA, "source_lock_sha256": RAW_LOCK_SHA,
              "specifications_sha256": lock["specifications_sha256"], "sdk_revision": job["sdk_revision"],
              "method_revision": job["method_revision"], "oracle_version": VERSION, "oracle_sha256": ORACLE,
              "cases": cases, "controls": controls, "prior_locked_cases": len(SLOTS),
              "source_omissions": SOURCE_OMISSIONS, "original_specs_and_payloads_shared": 0,
              "new_independent_cases": 0, "original_fcstd_conversions": 0, "whole_source_conversions": 0}

    def run_control(label):
        try:
            controls[label] = phase_receipt(control(directory, label, path), identities)
        except Exception as error:
            print_exc()
            controls[label] = {"passed": False, "error_type": type(error).__name__}

    try:
        run_control("ControlBefore")
        if controls["ControlBefore"]["passed"]:
            for slot in SLOTS:
                build_row = staged[slot]
                row = cases[slot] = build_row | {"passed": False, "phases": {}}
                try:
                    native_case(root, slot, lock, specifications[slot], build_row, row, identities)
                except Exception as error:
                    print_exc()
                    row["error_type"] = type(error).__name__
    finally:
        run_control("ControlAfter")
    try:
        check_originals(lock)
        require(checked(path, CONTROL) == seed, "control custody differs")
        custody = True
    except Exception:
        print_exc()
        custody = False
    count = len(set(identities))
    healthy = all(row["passed"] for row in controls.values()) and count == len(identities)
    complete = sum(row["passed"] for row in cases.values()) if healthy and custody else 0
    passed = complete == len(SLOTS) and count == 3 * len(SLOTS) + 2
    report.update(passed=passed, controls_healthy=healthy, native_processes=count,
                  originals_and_specifications_unchanged=custody, complete_paired_regressions=complete if passed else 0)
    return {"passed": passed, "result_sha256": publish(packet / "Result.json", report),
            "complete_paired_regressions": report["complete_paired_regressions"]}
