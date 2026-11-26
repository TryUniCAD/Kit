"""Prepare an independently witnessed P03 source for the bounded Fusion Boss probe."""

from json import loads

from P03CandidateRequest import build_request, canonical_json, read_request, sha
from P03ConstraintGraph import perimeter, selected_graph
from PairedCaptureIntake import require
from RectanglePairEvidence import RECEIPTS, REVISION, SPECIFICATION_SHA256
from interchange.Features.FeatureKinds import NativeFeature
from interchange.document.Models.DocumentModel import CadDocument


SOURCE_FORMAT = "solidworks.sldprt"
VARIANT = "baseline-a"
DRIVERS = ("width_mm", "height_mm", "depth_mm")
REQUEST_BINDINGS = (
    "capture_revision",
    "source_json_sha256",
    "logical_json_sha256",
    "target_json_sha256",
    "source_evidence",
    "source_ordered_relations",
    "source_relation_provenance",
    "body_label_evidence",
    "target_operation",
)


def _span(provenance, kind):
    require(
        provenance is not None
        and provenance.adapter == SOURCE_FORMAT
        and bool(provenance.native_id),
        f"P03 {kind} has no SOLIDWORKS native owner",
    )
    (span,) = (item for item in provenance.spans if item.record_kind == kind)
    require(span.length > 0, f"P03 {kind} has no physical source extent")
    return [span.stream, span.offset, span.length, kind]


def _in_sketch(span, sketch_span):
    stream, start, length = sketch_span
    return (
        span[0] == stream
        and start <= span[1]
        and span[1] + span[2] <= start + length
    )


def _origin_witness(source, sketch, owner, loop, owner_span, source_evidence):
    lines, proxy, aliases = perimeter(source, sketch, loop)
    native_origin = proxy.attributes["native_origin_feature_id"]
    (origin,) = (
        feature
        for feature in source.feature_timeline
        if feature.provenance is not None
        and feature.provenance.native_id == str(native_origin)
    )
    require(
        isinstance(origin.definition, NativeFeature)
        and origin.definition.object_data.get("native_class")
        == "moOriginProfileFeature_c"
        and origin.kind == "reference"
        and origin.operation is None
        and not origin.suppressed
        and origin.order < owner.order,
        "P03 fixed proxy has no unique active native Origin owner",
    )
    origin_span = _span(origin.provenance, "feature-record")
    proxy_span = _span(proxy.provenance, "sketch-point")
    (anchor,) = (
        rule
        for rule in sketch.constraints
        if rule.id == source_evidence["saved_relations"][-1]
    )
    anchor_span = _span(anchor.provenance, "sketch-origin-coincidence")
    (corner,) = (entity for entity in sketch.entities if entity.id == aliases[0])
    proxy_point = proxy.attributes["native_point_id"]
    corner_point = corner.attributes["native_point_id"]
    native_handle = proxy.attributes["native_origin_point_handle"]
    handles = anchor.attributes["native_point_handles"]
    operands = [[ref.entity_id, ref.point] for ref in anchor.references]
    require(
        origin_span[0] == owner_span[0]
        and _in_sketch(proxy_span, owner_span)
        and _in_sketch(anchor_span, owner_span)
        and native_handle == (0, -1, 0)
        and proxy_point != corner_point
        and anchor.attributes["native_code"] == 9
        and anchor.attributes["native_origin_feature_id"] == native_origin
        and anchor.attributes["native_point_ids"] == (proxy_point, corner_point)
        and len(handles) == len(set(handles)) == 2
        and operands == [[proxy.id, ""], [lines[0].id, "start"]],
        "P03 Origin proxy and saved anchor do not bind the exact corner operands",
    )
    return {
        "feature_id": origin.id,
        "native_id": origin.provenance.native_id,
        "native_class": origin.definition.object_data["native_class"],
        "feature_span": origin_span,
        "proxy_id": proxy.id,
        "proxy_span": proxy_span,
        "proxy_native_point": proxy_point,
        "external_point_handle": native_handle,
        "corner_alias_id": corner.id,
        "corner_native_point": corner_point,
        "anchor_id": anchor.id,
        "anchor_span": anchor_span,
        "anchor_native_point_handles": handles,
        "anchor_ordered_operands": operands,
    }


def _support_witness(source, sketch, owner, plane, owner_span):
    (datum,) = (
        feature
        for feature in source.feature_timeline
        if feature.id in owner.input_feature_ids
    )
    pointer = _span(sketch.provenance, "sketch-support-reference")
    datum_span = _span(datum.provenance, "feature-record")
    frame_span = _span(plane.provenance, "support-plane-frame")
    require(
        isinstance(datum.definition, NativeFeature)
        and datum.definition.object_data.get("native_class") == "moRefPlane_c"
        and datum_span[0] == frame_span[0] == owner_span[0]
        and _in_sketch(pointer, owner_span)
        and (plane.transform.z_axis.x, plane.transform.z_axis.y, plane.transform.z_axis.z)
        == (0, 0, 1),
        "P03 saved Front frame and support pointer do not bind its sketch",
    )
    return {
        "sketch_owner": owner.id,
        "sketch_id": sketch.id,
        "owner_span": owner_span,
        "datum_feature_id": datum.id,
        "datum_span": datum_span,
        "support_plane_id": plane.id,
        "frame_span": frame_span,
        "sketch_support_span": pointer,
    }


def _native_remainder(source):
    return {
        "native_definitions": [
            {
                "id": feature.id,
                "native_class": feature.definition.object_data.get("native_class"),
            }
            for feature in source.feature_timeline
            if isinstance(feature.definition, NativeFeature)
        ],
        "selection_ids": [selection.id for selection in source.selections],
        "has_brep": source.brep is not None,
        "brep_payload_count": len(source.brep_payloads),
        "diagnostic_count": len(source.diagnostics),
        "whole_source_admission": False,
    }


def prepare_request(source_json: bytes, logical_json: bytes) -> tuple[bytes, dict]:
    payload = build_request(source_json, logical_json)
    request_digest = sha(payload)
    record, _ = read_request(payload, request_digest)
    evidence = record["source_evidence"]

    source = CadDocument.from_json(source_json.decode("utf-8"))
    require(source.source.format_id == SOURCE_FORMAT, "P03 source is not SOLIDWORKS")
    sketch, owner, boss, plane, loop, owner_span = selected_graph(source)
    (body,) = source.bodies
    receipt_path, receipt_sha = RECEIPTS["P03"]["solidworks"]
    witness = {
        **{key: record[key] for key in REQUEST_BINDINGS},
        "request_sha256": request_digest,
        "source_archive_sha256": source.source.sha256,
        "source_specification_sha256": SPECIFICATION_SHA256,
        "source_receipt": {"path": receipt_path, "sha256": receipt_sha},
        "source_measurement_phase": "separate_process_reopen",
        "variant": VARIANT,
        "dimensions_mm": {
            parameter.name: parameter.value.value for parameter in source.parameters
        },
        "names": {"sketch": sketch.name, "boss": boss.name, "body": body.name},
        "origin": _origin_witness(source, sketch, owner, loop, owner_span, evidence),
        "support": _support_witness(source, sketch, owner, plane, owner_span),
        "native_remainder": _native_remainder(source),
    }
    return payload, loads(canonical_json(witness))


def _matches_target(target, witness):
    names = witness["names"]
    (sketch,) = target.sketches
    (body,) = target.bodies
    (boss,) = (feature for feature in target.feature_timeline if feature.operation)
    saved_ids = witness["source_evidence"]["saved_relations"]
    saved_rules = [
        [
            rule.id,
            rule.kind,
            [[ref.entity_id, ref.point] for ref in rule.references],
            rule.parameter_id,
        ]
        for rule in sketch.constraints
        if rule.id in saved_ids
    ]
    dimensions = {
        parameter.name: parameter.value.value
        for parameter in target.parameters
        if parameter.value.unit == "mm"
    }
    return (
        set(dimensions) == set(DRIVERS)
        and dimensions == witness["dimensions_mm"]
        and sketch.name == names["sketch"]
        and boss.name == names["boss"]
        and names["body"] == witness["body_label_evidence"]["sdk_unbound_label"]
        and body.name == witness["body_label_evidence"]["saved_compatibility_label"]
        and body.final_feature_id == boss.id
        and str(boss.operation) == witness["target_operation"] == "create"
        and saved_rules == witness["source_ordered_relations"]
        and saved_rules[-1][2] == witness["origin"]["anchor_ordered_operands"]
    )


def read_replay_input(payload: bytes, expected_sha256: str, witness: dict):
    record, target = read_request(payload, expected_sha256)
    require(
        all(record[key] == witness[key] for key in REQUEST_BINDINGS)
        and record["capture_revision"] == REVISION
        and record["source_evidence"]["source_sha256"]
        == witness["source_archive_sha256"]
        and record["source_evidence"]["source_operation"] == "join"
        and witness["variant"] == VARIANT
        and expected_sha256 == witness["request_sha256"]
        and _matches_target(target, witness),
        "P03 replay request differs from the independently prepared source witness",
    )
    return record, target
