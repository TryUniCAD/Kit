from __future__ import annotations

import argparse
from copy import deepcopy
import json
import math
from pathlib import Path, PureWindowsPath


def require(value, message):
    if not value:
        raise ValueError(message)


def part_geometry(values, edited_depth=None):
    document = values["document"]
    require(document["units"]["value"] == "mm", "the independent nested predictor requires declared millimetre part geometry")
    sketch, = document["sketches"]["$tuple"]
    feature, = document["feature_timeline"]["$tuple"]
    plane, = [row for row in document["support_planes"]["$tuple"] if row["id"] == sketch["support_plane_id"]]
    transform = plane["transform"]
    require(all([transform[name][axis] for axis in ("x", "y", "z")] == expected for name, expected in
                (("origin", [0.0, 0.0, 0.0]), ("x_axis", [1.0, 0.0, 0.0]), ("y_axis", [0.0, 1.0, 0.0]), ("z_axis", [0.0, 0.0, 1.0]))),
            "the independent predictor requires the actual front origin profile frame")
    require(feature["definition"]["end_condition"]["value"] == "blind"
            and not feature["definition"]["reversed"] and not feature["definition"]["symmetric"],
            "the independent predictor admits one forward blind profile")
    entities = sketch["entities"]["$tuple"]
    require(len(entities) >= 3 and all(row["kind"]["value"] == "line" for row in entities), "the predictor requires the actual closed line loop")
    vertices = [[row["geometry"]["start"][axis] * 0.001 for axis in ("x", "y")] for row in entities]
    require(all([row["geometry"]["end"][axis] * 0.001 for axis in ("x", "y")] == vertices[(index + 1) % len(vertices)]
                for index, row in enumerate(entities)), "the neutral line loop is not closed in authored order")
    cross = [a[0] * b[1] - b[0] * a[1] for a, b in zip(vertices, vertices[1:] + vertices[:1], strict=True)]
    twice_area = math.fsum(cross)
    require(abs(twice_area) > 0, "the authored profile has zero area")
    centroid = [math.fsum((a[axis] + b[axis]) * weight for a, b, weight in zip(vertices, vertices[1:] + vertices[:1], cross, strict=True)) / (3 * twice_area) for axis in range(2)]
    perimeter = math.fsum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(vertices, vertices[1:] + vertices[:1], strict=True))
    length = feature["definition"]["length"]
    require(length["unit"] == "mm" and length["value"] > 0, "the authored depth must be a positive millimetre length")
    depth = length["value"] * 0.001 if edited_depth is None else edited_depth
    area = abs(twice_area) * 0.5
    config, = document["configurations"]["$tuple"]
    require(config["active"], "the plain child needs its independent active configuration")
    parameter_ids = sketch["parameter_ids"]["$tuple"]
    dims = {"D1@" + sketch["name"]: None, "D2@" + sketch["name"]: None}
    if parameter_ids:
        by_id = {row["id"]: row for row in document["parameters"]["$tuple"]}
        params = [by_id[identity] for identity in parameter_ids]
        bounds = [max(point[axis] for point in vertices) - min(point[axis] for point in vertices) for axis in (0, 1)]
        require(len(vertices) == 4 and len(params) == 2 and all(
            row["owner_id"] == sketch["id"] and row["value"]["unit"] == "mm"
            and math.isclose(row["value"]["value"] * 0.001, bound, rel_tol=1e-12, abs_tol=1e-14)
            for row, bound in zip(params, bounds, strict=True)
        ), "independent sketch dimensions disagree with the neutral rectangle geometry")
        dims = {row["name"] + "@" + sketch["name"]: row["value"]["value"] * 0.001 for row in params}
    return {"volume": area * depth, "area": 2 * area + perimeter * depth, "com": [*centroid, depth / 2], "body_count": 1,
            "depth_m": depth, "parameters_m": {"D1@" + feature["name"]: depth, **dims},
            "configuration": config["name"], "name": document["metadata"]["name"]}


def matrix(frame):
    u, v = frame["u"], frame["v"]
    n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
    require(all(math.isclose(math.fsum(a * b for a, b in zip(left, right, strict=True)), expected, abs_tol=1e-12)
                for left, right, expected in ((u, u, 1.0), (v, v, 1.0), (u, v, 0.0))), "the prediction requires authored proper rigid frames")
    return [*u, *v, *n, *frame["origin"], 1.0, 0.0, 0.0, 0.0]


def compose(local, parent):
    rotation = [math.fsum(local[row * 3 + inner] * parent[inner * 3 + column] for inner in range(3)) for row in range(3) for column in range(3)]
    origin = [math.fsum(local[9 + inner] * parent[inner * 3 + column] for inner in range(3)) + parent[9 + column] for column in range(3)]
    return [*rotation, *origin, 1.0, 0.0, 0.0, 0.0]


def apply(transform, point):
    return [math.fsum(point[row] * transform[row * 3 + column] for row in range(3)) + transform[9 + column] for column in range(3)]


def predict(request, *, edit_part=None, edit_depth=None):
    definitions = {row["id"]: row for row in request["definitions"]}
    require(len(definitions) == len(request["definitions"]), "prediction needs unique complete definition identities")
    parts = {identity: part_geometry(row["request"], edit_depth if identity == edit_part else None) for identity, row in definitions.items() if row["kind"] == "part"}
    identity = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
    occurrences, leaves, active = [], [], set()

    def visit(name, transform, path):
        require(name not in active, "independent prediction rejects cyclic definitions")
        row = definitions[name]
        if row["kind"] == "part":
            geometry = parts[name]
            leaves.append({"definition": name, "path": path, "transform": transform, "volume": geometry["volume"], "area": geometry["area"], "com": apply(transform, geometry["com"])})
            return
        active.add(name)
        for item in row["occurrences"]:
            child = item["target"]
            pose = compose(matrix(item["occurrence"]), transform)
            child_path = [*path, item["occurrence"]["name"]]
            child_row = definitions[child]
            config = parts[child]["configuration"] if child_row["kind"] == "part" else child_row["request"]["configuration_name"]
            occurrences.append({"path": child_path, "definition": child, "kind": child_row["kind"], "configuration": config, "fixed": False, "transform": pose})
            visit(child, pose, child_path)
        active.remove(name)

    visit(request["root"], identity, [])
    volume = math.fsum(row["volume"] for row in leaves)
    require(volume > 0, "a populated nested prediction requires at least one solid")
    center = [math.fsum(row["volume"] * row["com"][axis] for row in leaves) / volume for axis in range(3)]
    root = definitions[request["root"]]
    return {"root": request["root"], "root_name": root["request"]["name"], "configuration": root["request"]["configuration_name"],
            "direct_occurrences": len(root["occurrences"]), "expanded_occurrences": len(occurrences), "body_count": len(leaves),
            "assembly": {"volume": volume, "area": math.fsum(row["area"] for row in leaves), "com": center}, "parts": parts,
            "occurrences": occurrences, "leaf_occurrences": leaves, "writer_frames_or_readback_used": False, "heldout_inputs_read": 0}


def main():
    parser = argparse.ArgumentParser(description="Independently predict SDK nested geometry from the actual authored neutral definition DAG")
    parser.add_argument("request", type=Path)
    parser.add_argument("--edit-part")
    parser.add_argument("--edit-depth-m", type=float)
    args = parser.parse_args()
    print(json.dumps(predict(json.loads(args.request.read_bytes()), edit_part=args.edit_part, edit_depth=args.edit_depth_m), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
