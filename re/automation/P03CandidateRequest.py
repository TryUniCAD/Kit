"""Bind one pinned saved profile to a source-free research Boss constructor request."""

from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "re/automation")]

from P03ConstraintIntent import REVISION, logical_summary, pinned_source_evidence
from P03ConstraintGraph import project_source
from ApplicationWorkers.ApplicationProtocol import write_new
from ContentManager import CONTENT_MANAGER, ReadContentManager
from PairedCaptureIntake import require
from VerifyContentManager import CheckContentContext
from convert.adapters.solidworks.Container.Container import SldprtArchive
from interchange.document.Models.DocumentModel import CadDocument


def canonical_json(value):
    return (
        dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def sha(raw):
    return sha256(raw).hexdigest()


def saved_body(raw, source, observed):
    archive = SldprtArchive.from_bytes(raw)
    payload = archive.require(CONTENT_MANAGER)
    content = ReadContentManager(19000, payload)
    CheckContentContext(archive, content, observed, 19000)
    (body,) = source.bodies
    (producer,) = [
        feature
        for feature in source.feature_timeline
        if feature.id == body.final_feature_id
    ]
    require(
        body.provenance is None
        and body.attributes.get("native_object_id") is None
        and content.Body is not None
        and content.Body.Visible
        and content.Body.Name == producer.name,
        "P03 saved compatibility label does not match the producing Boss and unbound SDK label",
    )
    return {
        "sdk_unbound_label": body.name,
        "saved_compatibility_label": content.Body.Name,
        "saved_compatibility_atom": content.Body.AtomId,
        "saved_compatibility_sha256": sha(payload),
        "producer": producer.id,
    }


def saved_relation_evidence(sketch, relation_ids):
    ordered = []
    for rule in sketch.constraints:
        if rule.id not in relation_ids:
            continue
        proof = rule.provenance
        require(
            proof is not None, "P03 saved relation is missing its source record span"
        )
        ordered.append(
            {
                "id": rule.id,
                "adapter": proof.adapter,
                "native_id": proof.native_id,
                "spans": [
                    [span.stream, span.offset, span.length, span.record_kind]
                    for span in proof.spans
                ],
            }
        )
    require(
        [rule["id"] for rule in ordered] == relation_ids,
        "P03 saved relation span order changed",
    )
    return ordered


def build_request(source_json, logical_json):
    raw, reference, observed = pinned_source_evidence()
    supplied = CadDocument.from_json(source_json.decode("utf-8"))
    require(
        supplied.to_json() == reference.to_json(),
        "P03 source JSON differs from the exact pinned strict read",
    )
    logical, source_evidence = project_source(supplied)
    persisted = CadDocument.from_json(logical_json.decode("utf-8"))
    require(
        persisted.to_json() == logical.to_json(),
        "P03 logical input differs from the proved source projection",
    )
    body_report = saved_body(raw, supplied, observed)
    (body,) = logical.bodies
    (sketch,) = logical.sketches
    marked = set(source_evidence["inferred_join_ids"])
    rules = tuple(
        replace(rule, attributes={}) if rule.id in marked else rule
        for rule in sketch.constraints
    )
    target = replace(
        logical,
        bodies=(replace(body, name=body_report["saved_compatibility_label"]),),
        sketches=(replace(sketch, constraints=rules),),
    )
    require(
        marked
        == {
            rule.id
            for rule in sketch.constraints
            if rule.attributes == {"inferred": True}
        },
        "P03 closure annotations differ from the checked source aliases",
    )
    target_json = target.to_json()
    return canonical_json(
        {
            "capture_revision": REVISION,
            "source_json_sha256": sha(source_json),
            "logical_json_sha256": sha(logical_json),
            "target_json_sha256": sha(target_json.encode("utf-8")),
            "source_evidence": source_evidence,
            "source_ordered_relations": logical_summary(logical)[
                "ordered_solver_relations"
            ],
            "source_relation_provenance": saved_relation_evidence(
                supplied.sketches[0], source_evidence["saved_relations"]
            ),
            "body_label_evidence": body_report,
            "target_operation": str(target.feature_timeline[1].operation),
            "target_document": target_json,
        }
    )


def read_request(payload, expected_sha256):
    require(
        sha(payload) == expected_sha256,
        "P03 request does not match the separately retained SHA-256",
    )
    record = loads(payload)
    require(canonical_json(record) == payload, "P03 request is not canonical")
    target = record["target_document"]
    require(
        sha(target.encode("utf-8")) == record["target_json_sha256"],
        "P03 target JSON differs from its retained digest",
    )
    return record, CadDocument.from_json(target)


def bind_source_keyword_order(record, target, context):
    from BossInput import ProjectBoss

    logical = ProjectBoss(target)
    width = (logical.Width.RelationId, logical.Width.Length.ParameterId)
    height = (logical.Height.RelationId, logical.Height.Length.ParameterId)
    (sketch,) = target.sketches
    driving = [
        [
            rule.id,
            rule.kind,
            [[ref.entity_id, ref.point] for ref in rule.references],
            rule.parameter_id,
        ]
        for rule in sketch.constraints
        if rule.kind == "distance"
    ]
    source_rows = [
        row for row in record["source_ordered_relations"] if row[1] == "distance"
    ]
    order = tuple((row[0], row[3]) for row in driving)
    require(
        source_rows == driving and order in ((width, height), (height, width)),
        "P03 keyword order differs from the two ordered source driving dimensions",
    )
    return replace(
        context, Package=replace(context.Package, WidthFirst=order == (width, height))
    )


def generate_request(
    payload, expected_sha256, context, *, candidate=None, preserve_keyword_order=False
):
    from VerifyFreshBoss import VerifyPortableBoss

    record, target = read_request(payload, expected_sha256)
    require(type(preserve_keyword_order) is bool, "P03 keyword-order selection must be a Boolean")
    if preserve_keyword_order:
        context = bind_source_keyword_order(record, target, context)
    observed = VerifyPortableBoss(target, context, Candidate=candidate)
    return {
        "request_sha256": expected_sha256,
        "source_operation": record["source_evidence"]["source_operation"],
        "target_operation": record["target_operation"],
        "body_label_evidence": record["body_label_evidence"],
        "candidate": observed,
        "vendor_loadable": False,
        "application_usable": False,
    }


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--source-json", type=Path, required=True)
    parser.add_argument("--logical-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError("P03 request destination already exists")
    source_json, logical_json = (
        args.source_json.read_bytes(),
        args.logical_json.read_bytes(),
    )
    payload = build_request(source_json, logical_json)
    require(
        (args.source_json.read_bytes(), args.logical_json.read_bytes())
        == (source_json, logical_json),
        "P03 input changed during candidate preparation",
    )
    write_new(args.output, payload)
    print(dumps({"request_sha256": sha(payload)}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (AttributeError, KeyError, TypeError, ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
