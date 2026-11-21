import math
from itertools import product

from NativeAcceptance.NeutralBrep import NeutralBrep
from NativeAcceptance.NeutralSemantics import Expression, NeutralSemantics, ParameterNames, Scalar


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


def Category(value):
    if type(value) in (int, float):
        return "number"
    if isinstance(value, dict):
        return tuple((key, Category(value[key])) for key in sorted(value))
    if isinstance(value, (tuple, list)):
        return tuple(sorted((Category(item) for item in value), key=repr))
    return type(value).__name__, value


def Anchor(value):
    if isinstance(value, (tuple, list)):
        if len(value) == 3 and all(type(item) in (int, float) and math.isfinite(item) for item in value):
            return tuple(value)
        positions = [Anchor(item) for item in value]
    elif isinstance(value, dict):
        if "start_mm" in value and "end_mm" in value:
            positions = [Anchor(value["start_mm"]), Anchor(value["end_mm"])]
        else:
            for key in ("point_mm", "center_mm", "geometry", "operands", "loops", "boundary", "origin_mm"):
                if key in value:
                    return Anchor(value[key])
            return None
    else:
        return None
    positions = [item for item in positions if item is not None]
    return tuple(math.fsum(item[axis] for item in positions) / len(positions) for axis in range(3)) if positions else None


def Magnitude(value):
    if type(value) in (int, float):
        if not math.isfinite(value):
            raise ValueError("semantic comparison requires finite numbers")
        return abs(value)
    if isinstance(value, dict):
        return max((Magnitude(item) for item in value.values()), default=0)
    if isinstance(value, (list, tuple)):
        return max((Magnitude(item) for item in value), default=0)
    return 0


def UnorderedEqual(left, right, unique=False):
    if not isinstance(left, (list, tuple)) or not isinstance(right, (list, tuple)) or len(left) != len(right):
        return False
    if len(left) > 16384:
        raise ValueError("semantic comparison inventory exceeds 16384 entries")
    left_positions = [Anchor(item) for item in left]
    right_positions = [Anchor(item) for item in right]
    tolerance = max(1e-6, max(Magnitude(left), Magnitude(right)) * 1e-9)
    buckets = {}
    for index, (item, position) in enumerate(zip(right, right_positions)):
        cell = None if position is None else tuple(math.floor(value / tolerance) for value in position)
        buckets.setdefault((Category(item), cell), {})[index] = item
    for item, position in zip(left, left_positions):
        category = Category(item)
        cells = [None] if position is None else product(*(range(math.floor(value / tolerance) - 1, math.floor(value / tolerance) + 2) for value in position))
        found = None
        attempts = 0
        for cell in cells:
            candidates = buckets.get((category, cell), {})
            for index, other in candidates.items():
                attempts += 1
                if attempts > 256:
                    raise ValueError("semantic comparison has more than 256 ambiguous spatial matches")
                if SemanticEqual(item, other):
                    if found is not None:
                        return False
                    found = candidates, index
                    if not unique:
                        break
            if found is not None and not unique:
                break
        if found is None:
            return False
        del found[0][found[1]]
    return True


def SemanticEqual(left, right):
    if not isinstance(left, dict) or not isinstance(right, dict):
        return SameValues(left, right)
    if left.keys() != right.keys():
        return False
    unordered = {"entities", "constraints", "dependencies", "vertices_mm", "edges", "faces", "loops"}
    for key in left:
        if key in unordered:
            if key == "loops":
                if len(left[key]) != len(right[key]):
                    return False
                if not UnorderedEqual([{"boundary": boundary} for boundary in left[key]], [{"boundary": boundary} for boundary in right[key]]):
                    return False
            elif not UnorderedEqual(left[key], right[key]):
                return False
        elif key in ("start_mm", "end_mm") and "start_mm" in left and "end_mm" in left and left.get("kind") != "arc":
            if not ((SameValues(left["start_mm"], right["start_mm"]) and SameValues(left["end_mm"], right["end_mm"])) or (SameValues(left["start_mm"], right["end_mm"]) and SameValues(left["end_mm"], right["start_mm"]))):
                return False
        elif key == "normal" and "offset_mm" in left:
            if not ((SameValues(left[key], right[key]) and NumericEqual(left["offset_mm"], right["offset_mm"])) or (SameValues(left[key], [-value for value in right[key]]) and NumericEqual(left["offset_mm"], -right["offset_mm"]))):
                return False
        elif key == "offset_mm" and "normal" in left:
            continue
        elif key == "boundary":
            if not UnorderedEqual(left[key], right[key]):
                return False
        elif key == "geometry" and left.get("kind") == "arc":
            if not SameValues(left[key], right[key]):
                return False
        elif not SemanticEqual(left[key], right[key]):
            return False
    return True


def CompareDocument(document, native, application):
    checks = []

    def Compare(field, expected, actual, numeric=False):
        missing = expected is None or actual is None
        passed = not missing and (NumericEqual(expected, actual) if numeric else SemanticEqual(expected, actual))
        checks.append({"field": field, "expected": expected, "actual": actual, "status": "unavailable" if missing else "passed" if passed else "failed"})

    bodies = native["bodies"]
    Compare("body_count", len(document.bodies), len(bodies))
    Compare("volume_mm3", sum(body.topology.volume for body in document.bodies) if document.bodies and all(body.topology.volume is not None for body in document.bodies) else None, sum(body["volume_mm3"] for body in bodies) if bodies else None, True)
    Compare("feature_tree", [[item.name, item.suppressed] for item in document.feature_timeline], [[item["name"], item["suppressed"]] for item in native["features"]])
    if application == "solidworks":
        Compare("feature_types", [item.attributes.get("native_type") for item in document.feature_timeline], [item["type"] for item in native["features"]])
        active = [item.name for item in document.configurations if item.active]
        Compare("active_configuration", active[0] if len(active) == 1 else None, native.get("configuration"))
    names = ParameterNames(document, application)
    expected = {names[item.id]: Scalar(item.value) for item in document.parameters}
    factors = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4, "ft": 304.8, "rad": 1.0, "deg": math.pi / 180, "": 1.0}
    actual = {}
    for item in native["parameters"]:
        name = item["name"]
        unit = item.get("value_unit", item["unit"])
        value = item["value"] * factors[unit] if unit in factors and type(item["value"]) in (int, float) else None
        if name in actual:
            raise ValueError("native parameter names are ambiguous")
        actual[name] = value
    Compare("parameter_names", sorted(expected), sorted(actual))
    for name, value in expected.items():
        Compare("parameter:" + name, value, actual.get(name), True)
    semantics = NeutralSemantics(document, application)
    observed = native.get("semantics")
    if observed is None or observed.get("schema") != 1:
        Compare("semantic_snapshot", None, observed)
    else:
        for group in ("features", "sketches", "parameters"):
            rows = observed.get(group)
            expected_names = [item["name"] for item in semantics[group]]
            observed_names = [item["name"] for item in rows] if isinstance(rows, list) else None
            Compare("semantic_" + group + "_inventory", expected_names if group == "features" else sorted(expected_names), observed_names if group == "features" or observed_names is None else sorted(observed_names))
            if not isinstance(rows, list):
                continue
            by_name = {item["name"]: item for item in rows}
            if len(by_name) != len(rows):
                raise ValueError("native semantic names are ambiguous")
            for row in semantics[group]:
                other = by_name.get(row["name"])
                if group == "sketches":
                    for label, sketch in (("decoded", row), ("native", other)):
                        entities = None if sketch is None else sketch.get("entities")
                        unique = isinstance(entities, list) and UnorderedEqual(entities, entities, unique=True)
                        Compare(label + ":sketch:" + row["name"] + ":entity_identity", True, True if unique else None)
                if group == "parameters" and other is not None:
                    other = {**other, "expression": Expression(other.get("expression"), other.get("dependencies", []))}
                Compare("semantic_" + group + ":" + row["name"], row, other)
        for gap in observed.get("gaps", ["collector_coverage"]):
            Compare("native:" + str(gap), None, None)
    gaps = []
    geometry, center = NeutralBrep(document, gaps)
    for gap in gaps + semantics["gaps"]:
        Compare("decoded:" + gap, None, None)
    if len(document.bodies) == len(bodies) == 1:
        topology = document.bodies[0].topology
        Compare("body_topology", {"faces": topology.face_count, "edges": topology.edge_count, "vertices": topology.vertex_count}, {key: bodies[0].get(key) for key in ("faces", "edges", "vertices")})
        Compare("body_geometry", geometry, bodies[0].get("geometry"))
        for label, boundary in (("decoded", geometry), ("native", bodies[0].get("geometry"))):
            for field in ("vertices_mm", "edges"):
                items = None if boundary is None else boundary.get(field)
                unique = isinstance(items, list) and UnorderedEqual(items, items, unique=True)
                Compare(label + ":brep:" + field + ":identity", True, True if unique else None)
        center = center if center is not None else document.bodies[0].attributes.get(application + ".body_centroid_mm")
        Compare("center_mm", None if center is None else list(center), bodies[0]["center_mm"])
    else:
        Compare("per_body_geometry", None, None)
    return checks
