from dataclasses import fields, is_dataclass, replace
from collections.abc import Mapping
from hashlib import sha256
import json

from interchange.Features.FeatureKinds import NativeFeature
from interchange.Records.RecordDiagnostic import Diagnostic
from interchange.Enums.EnumDocument import Severity


def canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode()


def identity(document):
    domains = (
        "configurations",
        "parameters",
        "support_planes",
        "sketches",
        "selections",
        "feature_timeline",
        "bodies",
    )
    result = {
        name: tuple(value.id for value in getattr(document, name)) for name in domains
    }
    result["sketch_entities"] = tuple(
        (sketch.id, tuple(value.id for value in sketch.entities))
        for sketch in document.sketches
    )
    result["sketch_relations"] = tuple(
        (sketch.id, tuple(value.id for value in sketch.constraints))
        for sketch in document.sketches
    )
    return result


def native_role(feature):
    attributes = feature.attributes
    definition = feature.definition
    data = definition.object_data if isinstance(definition, NativeFeature) else {}
    return {
        "source_id": feature.id,
        "name": feature.name,
        "kind": str(feature.kind),
        "native_class": data.get("native_class", ""),
        "native_type": attributes.get("native_type", ""),
        "order": feature.order,
        "input_feature_ids": feature.input_feature_ids,
        "sketch_id": feature.sketch_id,
        "parameter_ids": feature.parameter_ids,
        "selection_ids": feature.selection_ids,
        "suppressed": feature.suppressed,
        "configuration_states": tuple(
            {
                "configuration_id": state.configuration_id,
                "suppressed": state.suppressed,
                "parameter_override_ids": state.parameter_override_ids,
            }
            for state in feature.configuration_states
        ),
    }


def attributes_inventory(document):
    result = []

    def visit(value, path):
        if is_dataclass(value):
            for field in fields(value):
                item = getattr(value, field.name)
                if field.name == "attributes" and item:
                    result.append(
                        {
                            "owner": path,
                            "keys": sorted(item),
                            "projection": "audited_not_replayed",
                        }
                    )
                elif field.name == "provenance" and item is not None:
                    result.append(
                        {
                            "owner": path + "/provenance",
                            "keys": ("adapter", "native_id", "confidence", "spans"),
                            "projection": "source_identity_only_not_native_allocation",
                        }
                    )
                elif field.name not in ("metadata", "brep", "brep_payloads"):
                    visit(item, path + "/" + field.name)
        elif isinstance(value, (tuple, list)):
            for index, item in enumerate(value):
                visit(item, path + "/" + str(index))

    visit(document, "document")
    return result


def clean_value(value):
    if is_dataclass(value):
        replacements = {}
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name == "attributes":
                replacements[field.name] = {}
            elif field.name == "provenance":
                replacements[field.name] = None
            else:
                replacements[field.name] = clean_value(item)
        return replace(value, **replacements)
    if isinstance(value, tuple):
        return tuple(clean_value(item) for item in value)
    if isinstance(value, Mapping):
        return {key: clean_value(item) for key, item in value.items()}
    if isinstance(value, bytes):
        raise ValueError(
            "native bytes must be classified before portable normalization"
        )
    return value


def normalize(document, shape):
    features = []
    rows = []
    for feature in document.feature_timeline:
        row = native_role(feature)
        rows.append(row)
        if isinstance(feature.definition, NativeFeature):
            definition = NativeFeature(
                feature.definition.format_id,
                feature.definition.type_id,
                {
                    "source_role": row["native_class"] or row["native_type"],
                    "source_semantics_qualified": False,
                },
            )
            feature = replace(feature, definition=definition)
        features.append(clean_value(feature))
    report = document.metadata.get("solidworks.typed_resolved_semantics", {})
    tree = report.get("native_tree", {})
    text = document.metadata.get("solidworks.part_text_properties", {})
    config_text = {
        value.id: dict(value.attributes.get("custom_properties", {}))
        for value in document.configurations
    }
    blocking = [
        {
            "owner": "system_presentation",
            "reason": "ordinary reader has not qualified this complete root layout",
            "observed_status": tree.get("status"),
            "diagnostic": tree.get("diagnostic"),
        },
        {
            "owner": "system_history",
            "reason": "constructor requires two operation rows and one support; source retains all 28 history owners and three datums",
        },
        {
            "owner": "source_provenance",
            "reason": "ordinary read exposes source hash and spans but not authored header biography history times or author",
        },
        {
            "owner": "style_units_and_appearance",
            "reason": "ordinary read does not expose effective drafting standard precision density scene material preferences or actual light attributes",
        },
        {
            "owner": "native_system_children",
            "reason": "note pair light rows and empty exploded manager remain native definitions rather than construction inputs",
        },
        {
            "owner": "body_caption",
            "reason": "portable body is named Body 1 while constructor admission requires creating-feature name",
        },
        {
            "owner": "sketch_incidence",
            "reason": "source lines retain actual unordered endpoint incidence; strict constructor requires directed contiguous loop and no native attributes",
        },
        {
            "owner": "circle_center",
            "reason": "typed free circle has a real point entity; strict circle projection admits one entity",
        },
        {
            "owner": "operation_links",
            "reason": "source stock is join and actual profile-parent links remain; strict constructor requires create and reduced parents",
        },
        {
            "owner": "direction_axes",
            "reason": "source has two actual standalone native N_Axis selections which preparation does not project",
        },
        {
            "owner": "source_metadata",
            "reason": "source identity configuration properties and retained provenance need explicit preservation policy rather than deletion",
        },
    ]
    if text.get("status") != "complete":
        blocking.append(
            {"owner": "text_properties", "reason": "text projection is not admitted"}
        )
    coverage = {
        "status": "source_equivalence_refused",
        "geometry_owners_projected": True,
        "native_acceptance": False,
        "held_out_evaluated": False,
        "public_writer_qualified": False,
        "source_identity": {
            "format_id": document.source.format_id,
            "sha256": document.source.sha256,
            "path": document.source.path,
        },
        "identity_inventory": identity(document),
        "ordered_source_history": rows,
        "metadata_keys": sorted(document.metadata),
        "attribute_inventory": attributes_inventory(document),
        "text_properties": {
            "status": text.get("status"),
            "document_summary": dict(document.metadata.get("document_summary", {})),
            "custom_properties": dict(document.metadata.get("custom_properties", {})),
            "configurations": config_text,
        },
        "selected_scope": shape["scope"],
        "body_bounds_policy": "preserve source observation separately; derive prediction from real mid-plane end; do not trust fallback 0..depth box",
        "cache_policy": "BRep payloads and full saved-source wrapper bytes are observation-only and never generation input",
        "blocking_owners": blocking,
        "automatic_scope_policy": "saved explicit selected-stock snapshot only; no continuous automatic selector is established",
    }
    base = replace(
        document,
        feature_timeline=tuple(features),
        source=replace(document.source, attributes={}),
        metadata={},
        brep=None,
        brep_payloads=(),
        diagnostics=(),
    )
    normalized = clean_value(base)
    configurations = tuple(
        replace(value, attributes={"custom_properties": config_text[value.id]})
        for value in normalized.configurations
    )
    normalized = replace(
        normalized,
        source=document.source,
        configurations=configurations,
        metadata={
            "document_summary": coverage["text_properties"]["document_summary"],
            "custom_properties": coverage["text_properties"]["custom_properties"],
            "source_projection": {
                "status": coverage["status"],
                "geometry_owners_projected": True,
                "unmapped_owner_roles": tuple(value["owner"] for value in blocking),
            },
        },
        diagnostics=(
            Diagnostic(
                "throughall.source_projection_incomplete",
                "source owner identities are retained but full original-source construction is refused",
                Severity.KInfo,
            ),
        ),
    )
    if identity(document) != identity(normalized):
        raise ValueError("normalization dropped or changed an actual source owner")
    normalized.assert_valid()
    if b'"$bytes"' in canonical(normalized.to_dict()):
        raise ValueError("normalized model retained native bytes")
    coverage["normalized_document_sha256"] = sha256(
        canonical(normalized.to_dict())
    ).hexdigest()
    coverage["source_owner_ids_preserved"] = True
    coverage["source_native_bytes_in_normalized_document"] = 0
    return normalized, coverage


def require_qualified(coverage):
    if coverage.get("status") != "complete" or coverage.get("blocking_owners"):
        raise ValueError("full original-source through-all coverage is not qualified")
