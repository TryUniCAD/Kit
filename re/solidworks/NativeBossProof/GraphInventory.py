from base64 import b64decode
from collections import Counter
from hashlib import sha256
import json


COLLECTIONS = (
    "configurations", "parameters", "support_planes", "sketches", "selections",
    "feature_timeline", "bodies", "materials", "meshes", "brep_payloads",
)


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def rows(value, name):
    result = value.get(name)
    if type(result) is not dict or set(result) != {"$tuple"} or type(result["$tuple"]) is not list:
        raise ValueError("missing typed collection: " + name)
    return result["$tuple"]


def value_kind(value):
    return value.get("value") if type(value) is dict and "$enum" in value else value


def summarize_bytes(value, path, spans):
    if type(value) is dict:
        if "$bytes" in value:
            if set(value) != {"$bytes"} or type(value["$bytes"]) is not str:
                raise ValueError("invalid typed byte span at " + path)
            payload = b64decode(value["$bytes"], validate=True)
            identity = {"bytes": len(payload), "sha256": sha256(payload).hexdigest()}
            spans.append({"path": path, **identity})
            return {"$retained_bytes": identity}
        return {name: summarize_bytes(item, path + "/" + name, spans) for name, item in sorted(value.items())}
    if type(value) is list:
        return [summarize_bytes(item, path + "/" + str(index), spans) for index, item in enumerate(value)]
    return value


def inspect_document(wire):
    spans = []
    sanitized = summarize_bytes(wire, "", spans)
    collections = {name: rows(wire, name) for name in COLLECTIONS}
    records = {}
    duplicate_ids = []
    for name, entries in collections.items():
        counts = Counter(entry.get("id") for entry in entries)
        duplicate_ids.extend({"collection": name, "id": identity, "count": count} for identity, count in counts.items() if count != 1)
        records[name] = [
            {
                "id": entry.get("id"), "name": entry.get("name"), "type": entry.get("$type"),
                "kind": value_kind(entry.get("kind")),
                "wire_sha256": digest(summarize_bytes(entry, "", [])),
            }
            for entry in entries
        ]
    features = collections["feature_timeline"]
    feature_index = {entry["id"]: entry for entry in features}
    parameters = {entry["id"]: entry for entry in collections["parameters"]}
    planes = {entry["id"]: entry for entry in collections["support_planes"]}
    sketches = {entry["id"]: entry for entry in collections["sketches"]}
    bodies = {entry["id"]: entry for entry in collections["bodies"]}
    links = []
    for feature in features:
        for identity in rows(feature, "input_feature_ids"):
            links.append({"owner": feature["id"], "relation": "input_feature", "target": identity, "resolved": identity in feature_index})
        for identity in rows(feature, "parameter_ids"):
            target = parameters.get(identity)
            links.append({"owner": feature["id"], "relation": "driving_parameter", "target": identity, "resolved": target is not None and target.get("owner_id") == feature["id"]})
        for identity in rows(feature, "output_body_ids"):
            target = bodies.get(identity)
            links.append({"owner": feature["id"], "relation": "output_body", "target": identity, "resolved": target is not None and target.get("final_feature_id") == feature["id"]})
        if feature.get("sketch_id") is not None:
            identity = feature["sketch_id"]
            links.append({"owner": feature["id"], "relation": "sketch", "target": identity, "resolved": identity in sketches})
    sketch_rows = []
    for sketch in sketches.values():
        identity = sketch.get("support_plane_id")
        links.append({"owner": sketch["id"], "relation": "support_plane", "target": identity, "resolved": identity in planes})
        entities = rows(sketch, "entities")
        sketch_rows.append({
            "id": sketch["id"], "name": sketch.get("name"), "support_plane_id": identity,
            "constraints": len(rows(sketch, "constraints")),
            "closed_profile_entity_ids": rows(sketch, "closed_profile_entity_ids"),
            "entities": [{
                "id": entry["id"], "kind": value_kind(entry.get("kind")),
                "geometry_type": entry.get("geometry", {}).get("$type"),
                "native_kind": entry.get("attributes", {}).get("native_kind"),
                "construction": entry.get("construction"), "fixed": entry.get("fixed"),
                "geometry": summarize_bytes(entry.get("geometry"), "", []),
            } for entry in entities],
        })
    for body in bodies.values():
        identity = body.get("final_feature_id")
        feature = feature_index.get(identity)
        links.append({"owner": body["id"], "relation": "final_feature", "target": identity, "resolved": feature is not None})
        links.append({"owner": body["id"], "relation": "final_feature_backlink", "target": identity, "resolved": feature is not None and body["id"] in rows(feature, "output_body_ids")})
    brep = wire.get("brep")
    brep_counts = {name: len(value.get("$tuple", [])) for name, value in (brep or {}).items() if type(value) is dict and "$tuple" in value}
    if brep is not None:
        for body in rows(brep, "bodies"):
            identity = body.get("design_body_id")
            links.append({"owner": body["id"], "relation": "brep_design_body", "target": identity, "resolved": identity in bodies})
    feature_rows = [{
        "id": entry["id"], "name": entry.get("name"), "kind": value_kind(entry.get("kind")),
        "native_type": entry.get("attributes", {}).get("native_type"),
        "native_id": entry.get("attributes", {}).get("native_object_id"),
        "definition_type": (entry.get("definition") or {}).get("$type"),
        "definition_length": (entry.get("definition") or {}).get("length"),
        "native_class": (entry.get("definition") or {}).get("object_data", {}).get("native_class"),
        "operation": value_kind(entry.get("operation")), "order": entry.get("order"),
        "suppressed": entry.get("suppressed"), "sketch_id": entry.get("sketch_id"),
        "input_feature_ids": rows(entry, "input_feature_ids"),
        "parameter_ids": rows(entry, "parameter_ids"), "output_body_ids": rows(entry, "output_body_ids"),
    } for entry in features]
    return {
        "document_sha256": digest(sanitized), "root_fields": sorted(wire),
        "counts": {name: len(entries) for name, entries in collections.items()},
        "records": records, "duplicate_ids": duplicate_ids, "features": feature_rows,
        "parameters": summarize_bytes(collections["parameters"], "", []),
        "body_summaries": summarize_bytes(collections["bodies"], "", []),
        "sketches": sketch_rows, "ownership_links": links,
        "unresolved_ownership_links": [entry for entry in links if not entry["resolved"]],
        "brep_counts": brep_counts, "retained_byte_spans": spans,
        "diagnostics": wire.get("diagnostics"), "native_property_status": wire.get("metadata", {}).get("solidworks.part_text_properties"),
    }


def compare_documents(left, right):
    changes = []
    for name in COLLECTIONS:
        first = {entry["id"]: entry for entry in left["records"][name]}
        second = {entry["id"]: entry for entry in right["records"][name]}
        for identity in sorted(first.keys() | second.keys()):
            if first.get(identity) != second.get(identity):
                changes.append({"collection": name, "id": identity, "left": first.get(identity), "right": second.get(identity)})
    return {
        "policy": "exact_typed_identity_without_ignored_fields",
        "equal": left["document_sha256"] == right["document_sha256"] and not left["duplicate_ids"] and not right["duplicate_ids"],
        "changed_records": changes,
        "ownership_changed": left["ownership_links"] != right["ownership_links"],
        "root_fields_changed": left["root_fields"] != right["root_fields"],
    }
