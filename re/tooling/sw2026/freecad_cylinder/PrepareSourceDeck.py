from argparse import ArgumentParser
from hashlib import sha256
import json
from math import isclose, isfinite, pi
from pathlib import Path


def digest(raw):
    return sha256(raw).hexdigest()


def checked(path, expected=None):
    data = path.read_bytes()
    if path.is_symlink() or (expected is not None and digest(data) != expected):
        raise ValueError(f"disclosed FreeCAD input changed: {path.name}")
    return data


def field_payload(properties, name, field_type, tag):
    field = properties[name]
    value, = field["children"]
    if field["attributes"].get("type") != field_type or value["tag"] != tag:
        raise ValueError(f"unsupported {name} owner in source cylinder")
    return value["attributes"]


def values(properties):
    radius, height, sweep = (
        float(field_payload(properties, name, kind, "Float")["value"])
        for name, kind in (("Radius", "App::PropertyLength"), ("Height", "App::PropertyLength"),
                           ("Angle", "App::PropertyAngle"))
    )
    placement = field_payload(properties, "Placement", "App::PropertyPlacement", "PropertyPlacement")
    position = tuple(float(placement[name]) for name in ("Px", "Py", "Pz"))
    quaternion = tuple(float(placement[name]) for name in ("Q0", "Q1", "Q2", "Q3"))
    if (not all(isfinite(x) and x > 0 for x in (radius, height)) or sweep != 360.0
            or position != (0.0, 0.0, 0.0) or quaternion != (0.0, 0.0, 0.0, 1.0)):
        raise ValueError("the first native cylinder cohort requires a full origin-aligned primitive")
    return radius, height


def case(root, row, index):
    name = row["name"]
    saved = checked(root / "Disclosed" / row["file"], row["file_sha256"])
    native = checked(root / "StrictNeutral02" / f"{name}.json")
    model = json.loads(native)
    feature, = model["feature_timeline"]["$tuple"]
    body, = model["bodies"]["$tuple"]
    definition = feature["definition"]
    parameters = model["parameters"]["$tuple"]
    if (len(saved) != row["bytes"] or model["source"]["sha256"] != row["file_sha256"]
            or definition["type_id"] != row["native_type"] or definition["type_id"] != "Part::Cylinder"
            or body["final_feature_id"] != feature["id"] or feature["suppressed"] is not False
            or model["sketches"]["$tuple"]
            or [item["id"] for item in parameters] != feature["parameter_ids"]["$tuple"]
            or any(item["owner_id"] != feature["id"] for item in parameters)):
        raise ValueError("strict FCStd projection lacks the unique primitive and live source ownership")
    radius, height = values(definition["object_data"]["properties"])
    if (radius, height) != (row["radius_mm"], row["height_mm"]):
        raise ValueError("neutral dimensions differ from the independently authored FreeCAD model")
    drivers = {}
    for target, number in (("Radius", radius), ("Height", height)):
        item, = (x for x in parameters if x["attributes"]["freecad_path"] == target)
        if (item["role"]["value"] != "driving" or item["expression"] is not None
                or item["value"]["kind"]["value"] != "length"
                or item["value"]["unit"] != "mm" or item["value"]["value"] != number):
            raise ValueError("neutral cylinder requires both actual editable length properties")
        drivers[target] = item["id"]
    shape = row["shape"]
    volume, area = pi * radius * radius * height, 2 * pi * radius * (radius + height)
    if (shape["solids"] != 1 or shape["faces"] != 3
            or not isclose(volume, shape["volume_mm3"], rel_tol=1e-12)
            or not isclose(area, shape["area_mm2"], rel_tol=1e-12)
            or any(not isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12)
                   for actual, expected in zip(shape["center_mm"], (0, 0, height / 2), strict=True))):
        raise ValueError("FreeCAD mass properties differ from the independent solid formula")
    return {
        "case": name, "source_sha256": row["file_sha256"], "strict_neutral_sha256": digest(native),
        "source_feature_id": feature["id"], "source_feature_name": feature["name"],
        "source_format": definition["format_id"], "source_type": definition["type_id"],
        "source_driver_ids": drivers,
        "native_spec": {
            "name": f"OriginCylinderD{index:02d}", "split": "discovery", "plane": "front",
            "profile": {"kind": "circle", "center_mm": [0.0, 0.0], "radius_mm": radius},
            "depth_mm": height, "dimension_kind": "radial", "end_condition": "blind",
            "reverse": False, "expected_bodies": 1, "export_siblings": True,
            "edit": {"target": "curve-0", "factor": (1.157, 0.887)[index - 1]},
        },
        "second_independent_edit": {"target": "depth", "factor": (0.827, 1.133)[index - 1]},
        "predicted_pristine": {"bodies": 1, "volume_mm3": volume, "area_mm2": area,
                               "center_mm": [0, 0, height / 2]},
    }


def main():
    parser = ArgumentParser(description="Prepare disclosed SOLIDWORKS source companions for actual FreeCAD cylinders")
    parser.add_argument("sources", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--freecad-author-sha256", required=True)
    args = parser.parse_args()
    root = args.sources.resolve(strict=True)
    report = json.loads(checked(root / "DisclosedAuthorResult.json", args.freecad_author_sha256))
    if (report["schema"] != "kit.sw2026.freecad-cylinder-disclosed-source.v1"
            or not report["passed"] or report["heldout_inputs_read"] or report["writer_outputs"]):
        raise ValueError("use independently authored disclosed FreeCAD source inputs")
    inputs = {row["name"]: row for row in report["cases"]}
    rows = [case(root, inputs[name], index) for index, name in enumerate(("CylinderA", "CylinderB"), 1)]
    packet = {"schema": "kit.sw2026.freecad-cylinder-native-source-deck.v1", "passed": True,
              "author_report_sha256": args.freecad_author_sha256,
              "deck_tool_sha256": digest(Path(__file__).read_bytes()),
              "freecad_application_version": report["application_version"], "cases": rows,
              "oracle_build": "34.5.2.0604", "authored_native_sources": 0,
              "native_processes_started": 0, "heldout_inputs_read": 0, "writer_outputs": 0}
    encoded = (json.dumps(packet, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with args.output.open("xb") as stream:
        stream.write(encoded)
    print(json.dumps({"passed": True, "cases": len(rows), "output_sha256": digest(encoded)}))


if __name__ == "__main__":
    main()
