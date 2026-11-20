import math


def NumericEqual(left, right):
    return type(left) in (int, float) and type(right) in (int, float) and math.isfinite(left) and math.isfinite(right) and math.isclose(left, right, rel_tol=1e-9, abs_tol=1e-6)


def SameValues(left, right):
    if type(left) in (int, float) and type(right) in (int, float):
        return NumericEqual(left, right)
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(SameValues(left[key], right[key]) for key in left)
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        return len(left) == len(right) and all(SameValues(a, b) for a, b in zip(left, right))
    return type(left) is type(right) and left == right


def CompareDocument(document, native, application):
    checks = []

    def Compare(field, expected, actual, numeric=False):
        missing = expected is None or actual is None
        passed = not missing and (NumericEqual(expected, actual) if numeric else SameValues(expected, actual))
        checks.append({"field": field, "expected": expected, "actual": actual, "status": "unavailable" if missing else "passed" if passed else "failed"})

    units = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4, "ft": 304.8, "rad": 1.0, "deg": math.pi / 180}
    bodies = native["bodies"]
    Compare("body_count", len(document.bodies), len(bodies))
    Compare("volume_mm3", sum(body.topology.volume for body in document.bodies) if document.bodies and all(body.topology.volume is not None for body in document.bodies) else None, sum(body["volume_mm3"] for body in bodies) if bodies else None, True)
    Compare("feature_tree", [[item.name, item.suppressed] for item in document.feature_timeline], [[item["name"], item["suppressed"]] for item in native["features"]])
    owners = {item.id: item.name for item in document.feature_timeline}
    expected = {}
    for item in document.parameters:
        name = item.name if application == "fusion" else f"{item.name}@{owners.get(item.owner_id, item.owner_id)}"
        if name in expected:
            raise ValueError("decoded parameter names are ambiguous")
        expected[name] = float(item.value.value) * units[item.value.unit] if type(item.value.value) in (int, float) and item.value.unit in units else None
    actual = {}
    for item in native["parameters"]:
        name = item["name"]
        value = item["value"] * units[item["unit"]] if item["unit"] in units else None
        if name in actual and not SameValues(value, actual[name]):
            raise ValueError("native parameter names are ambiguous")
        actual[name] = value
    Compare("parameter_names", sorted(expected), sorted(actual))
    for name, value in expected.items():
        Compare("parameter:" + name, value, actual.get(name), True)
    Compare("sketch_inventory", [{"name": item.name, "entities": len(item.entities), "constraints": len(item.constraints)} for item in document.sketches], [{key: item[key] for key in ("name", "entities", "constraints")} for item in native["sketches"]])
    if len(document.bodies) == len(bodies) == 1:
        center = document.bodies[0].attributes.get(application + ".body_centroid_mm")
        Compare("center_mm", None if center is None else list(center), bodies[0]["center_mm"])
    else:
        Compare("per_body_center_mm", None, [body["center_mm"] for body in bodies])
    return checks
