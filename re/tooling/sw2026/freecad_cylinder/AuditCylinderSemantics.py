import argparse
from collections import Counter
from hashlib import sha1, sha256
import json
from math import isfinite, pi, radians, tan
from pathlib import Path


def require(value, reason):
    if not value:
        raise ValueError(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def fingerprint(value):
    return sha256(canonical(value)).hexdigest()


def tuple_items(value):
    require(type(value) is dict and set(value) == {"$tuple"}, "expected an exact portable tuple")
    require(type(value["$tuple"]) is list, "portable tuple contents differ")
    return value["$tuple"]


def scalar_value(prop):
    children = prop.get("children", [])
    require(children and all(type(row) is dict for row in children), "scalar framing differs")
    kind = prop["attributes"]["type"]
    first = children[0]
    attrs = first["attributes"]
    if kind in ("App::PropertyAngle", "App::PropertyLength", "App::PropertyFloat"):
        require(len(children) == 1 and first["tag"] == "Float", "float framing differs")
        value = float(attrs["value"])
        require(isfinite(value), "nonfinite source scalar")
        return value
    if kind == "App::PropertyString":
        require(len(children) == 1 and first["tag"] == "String", "string framing differs")
        return attrs["value"]
    if kind == "App::PropertyBool":
        require(len(children) == 1 and first["tag"] == "Bool", "boolean framing differs")
        require(attrs["value"] in ("true", "false"), "invalid source boolean")
        return attrs["value"] == "true"
    require(kind == "App::PropertyEnumeration" and first["tag"] == "Integer", "unsupported scalar type")
    index = int(attrs["value"])
    if len(children) == 1:
        require(attrs.get("CustomEnum") != "true", "custom enum labels are absent")
        return index
    require(len(children) == 2 and attrs.get("CustomEnum") == "true", "enum framing differs")
    labels = children[1]
    values = labels.get("children", [])
    require(labels["tag"] == "CustomEnumList" and int(labels["attributes"]["count"]) == len(values),
            "enum label count differs")
    require(0 <= index < len(values) and all(row["tag"] == "Enum" for row in values), "enum selector differs")
    return values[index]["attributes"]["value"]


def source_pins(record, source_root):
    checked = []
    for source in record["sources"]:
        raw = (source_root / source["path"]).read_bytes()
        require(len(raw) == source["bytes"], "pinned source length differs: " + source["path"])
        require(sha256(raw).hexdigest() == source["sha256"], "pinned source SHA-256 differs: " + source["path"])
        blob = sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        require(blob == source["git_blob_sha1"], "pinned Git blob identity differs: " + source["path"])
        checked.append({"path": source["path"], "sha256": source["sha256"],
                        "git_blob_sha1": blob, "lines": len(raw.decode("utf-8").splitlines())})
    by_path = {row["path"]: row for row in checked}
    require(len(by_path) == len(checked), "duplicate pinned public source")
    for evidence in record["evidence"].values():
        source = by_path[evidence["path"]]
        require(1 <= evidence["start_line"] <= evidence["end_line"] <= source["lines"],
                "source evidence line range differs")
    return checked


def placement(properties, name):
    prop = properties[name]
    children = prop["children"]
    require(prop["attributes"]["type"] == "App::PropertyPlacement" and len(children) == 1
            and children[0]["tag"] == "PropertyPlacement", "placement ownership differs: " + name)
    value = {key: float(item) for key, item in children[0]["attributes"].items()}
    require(set(value) == {"A", "Ox", "Oy", "Oz", "Px", "Py", "Pz", "Q0", "Q1", "Q2", "Q3"}
            and all(isfinite(item) for item in value.values()), "placement framing differs")
    require([value[key] for key in ("Px", "Py", "Pz")] == [0.0, 0.0, 0.0]
            and [value[key] for key in ("Q0", "Q1", "Q2", "Q3")] == [0.0, 0.0, 0.0, 1.0]
            and value["A"] == 0.0, "disclosed placement is outside the declared identity profile")
    return {"property_sha256": fingerprint(prop), "position_mm": [value[key] for key in ("Px", "Py", "Pz")],
            "quaternion_xyzw": [value[key] for key in ("Q0", "Q1", "Q2", "Q3")]}


def case_audit(record, expected, path):
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == expected["neutral_sha256"], "declared disclosed neutral identity differs")
    doc = json.loads(raw)
    require(doc["$type"] == "CadDocument" and doc["source"]["format_id"] == "freecad.fcstd"
            and doc["source"]["sha256"] == expected["source_sha256"], "actual source identity differs")
    features = tuple_items(doc["feature_timeline"])
    require(len(features) == 1, "disclosed primitive history differs")
    feature = features[0]
    native = feature["definition"]["object_data"]
    require(feature["definition"]["type_id"] == native["type_id"] == "Part::Cylinder", "primitive owner differs")
    require(doc["metadata"]["freecad"]["objects"] == [native]
            and feature["attributes"]["freecad"] == native, "three actual native owner copies disagree")
    properties = native["properties"]
    field_names = [row["path"] for row in record["fields"]]
    nonscalar_names = [row["path"] for row in record["nonscalar_owners"]]
    require(len(field_names) == len(set(field_names)) == 13
            and set(properties) == set(field_names + nonscalar_names), "source property envelope differs")
    require(len(native["property_order"]) == len(set(native["property_order"])) == len(properties)
            and set(native["property_order"]) == set(properties), "actual property order is incomplete")
    parameters = tuple_items(doc["parameters"])
    require(len(parameters) == 13 and [row["id"] for row in parameters] == tuple_items(feature["parameter_ids"]),
            "all actual parameter identities/order must remain present")
    require([row["attributes"]["freecad_path"] for row in parameters] == field_names,
            "actual scalar source order differs")
    rows = []
    values = {}
    for semantic, parameter in zip(record["fields"], parameters):
        name = semantic["path"]
        prop = properties[name]
        require(prop["tag"] == "Property" and prop["attributes"]["name"] == name
                and prop["attributes"]["type"] == semantic["source_type"], "actual scalar type differs: " + name)
        require(parameter["attributes"] == {"freecad_path": name, "freecad_property": prop,
                                           "freecad_property_type": semantic["source_type"]},
                "actual scalar property provenance differs: " + name)
        require(parameter["id"] == "freecad:parameter:" + native["name"] + ":" + name
                and parameter["owner_id"] == feature["id"]
                and parameter["name"] == feature["name"] + "." + name, "parameter ownership differs: " + name)
        require(parameter["role"] == {"$enum": "ParameterRole", "value": "driving"}
                and parameter["expression"] is None, "recorded decoder role/expression differs: " + name)
        value = scalar_value(prop)
        portable = parameter["value"]
        require(type(value) is type(portable["value"]) and value == portable["value"]
                and portable["kind"] == {"$enum": "ValueKind", "value": semantic["portable_kind"]}
                and portable["unit"] == semantic["unit"], "portable scalar value/type/unit differs: " + name)
        rows.append({"path": name, "id": parameter["id"], "name": parameter["name"], "value": value,
                     "recorded_role": "driving", "semantic_class": semantic["semantic_class"],
                     "source_type": semantic["source_type"], "property_sha256": fingerprint(prop)})
        values[name] = value
    for semantic in record["nonscalar_owners"]:
        prop = properties[semantic["path"]]
        require(prop["attributes"]["type"] == semantic["source_type"], "nonscalar source owner differs")
    engines = record["rules"]["attacher_engine_classes"]
    require(values["AttacherEngine"] in engines and engines[values["AttacherEngine"]] == values["AttacherType"],
            "actual engine label and restored class disagree")
    require(values["Angle"] == 360.0 and values["FirstAngle"] == values["SecondAngle"] == 0.0,
            "disclosed source is outside full ordinary cylinder scope")
    require(values["MapMode"] == 0 and values["MapPathParameter"] == 0.0 and values["MapReversed"] is False,
            "disclosed source has active or unmeasured attachment inputs")
    for name, tag in (("AttachmentSupport", "LinkSubList"), ("ExpressionEngine", "ExpressionEngine")):
        children = properties[name]["children"]
        require(children == [{"attributes": {"count": "0"}, "tag": tag}], "nonempty source dependency owner")
    require(values["Label"] == feature["name"], "feature caption lost its actual label")
    radius, height = values["Radius"], values["Height"]
    require(radius > 0 and height > 0, "nonpositive disclosed geometry")
    vector = [height * tan(radians(values["FirstAngle"])), height * tan(radians(values["SecondAngle"])), height]
    return {"case_id": expected["case_id"], "neutral_sha256": expected["neutral_sha256"],
            "source_sha256": expected["source_sha256"], "native_object_sha256": fingerprint(native),
            "actual_parameter_rows": rows, "semantic_class_counts": dict(Counter(row["semantic_class"] for row in rows)),
            "property_order": native["property_order"], "nonscalar_envelope_sha256": fingerprint(
                {name: properties[name] for name in nonscalar_names}),
            "placements": {name: placement(properties, name) for name in ("Placement", "AttachmentOffset")},
            "independent_current_geometry": {"displacement_mm": vector, "volume_mm3": pi * radius * radius * height,
                                             "center_mm": [item * 0.5 for item in vector]},
            "full_document_sha256": fingerprint(doc), "native_mapping_qualified": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--case-a", type=Path, required=True)
    parser.add_argument("--case-b", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "output must be new")
    raw = args.record.read_bytes()
    record = json.loads(raw)
    require(record["schema"] == "kit.sw2026.freecad-cylinder-property-semantics.v1", "knowledge schema differs")
    require(record["authority"]["revision"] == "4fd3bf320d9566a27e60069fc8387448aaa3a094", "source revision differs")
    sources = source_pins(record, args.source_root)
    require([row["case_id"] for row in record["disclosed_inputs"]] == ["CylinderA", "CylinderB"],
            "only declared disclosed cases may be audited")
    cases = [case_audit(record, expected, path) for expected, path in zip(record["disclosed_inputs"], (args.case_a, args.case_b))]
    result = {"schema": "kit.sw2026.freecad-cylinder-property-semantics-audit.v1",
              "source_envelope_correlation_passed": True, "knowledge_sha256": sha256(raw).hexdigest(),
              "tool_sha256": sha256(Path(__file__).read_bytes()).hexdigest(), "authority_revision": record["authority"]["revision"],
              "pinned_source_count": len(sources), "pinned_sources": sources, "case_count": len(cases),
              "classified_scalar_owners": sum(len(row["actual_parameter_rows"]) for row in cases),
              "retained_nonscalar_owners": sum(len(row["property_order"]) - len(row["actual_parameter_rows"]) for row in cases),
              "cases": cases, "target_native_lowering_qualified": False,
              "generated_writer_outputs": 0, "native_processes_started": 0, "heldout_inputs_read": 0}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    args.output.write_bytes(encoded)
    print(json.dumps({"source_envelope_correlation_passed": True, "sha256": sha256(encoded).hexdigest(),
                      "pinned_source_count": len(sources), "classified_scalar_owners": result["classified_scalar_owners"],
                      "generated_writer_outputs": 0, "native_processes_started": 0, "heldout_inputs_read": 0}))


if __name__ == "__main__":
    main()
