from __future__ import annotations

import json
import math
import sys
from pathlib import PureWindowsPath


IDENTITY = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0)


def require(value, message):
    if not value:
        raise ValueError(message)


def matrix(placement):
    u, v = placement["u"], placement["v"]
    require(len(u) == len(v) == len(placement["origin"]) == 3 and
            all(math.isfinite(value) for axis in (u, v, placement["origin"]) for value in axis) and
            math.isclose(sum(value * value for value in u), 1.0, abs_tol=1e-12) and
            math.isclose(sum(value * value for value in v), 1.0, abs_tol=1e-12) and
            abs(sum(first * second for first, second in zip(u, v, strict=True))) < 1e-12, "prediction requires an explicit orthonormal rigid frame")
    normal = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    return (*u, *v, *normal, *placement["origin"], 1.0, 0.0, 0.0, 0.0)


def point(value, pose):
    return tuple(math.fsum(value[index] * pose[index * 3 + axis] for index in range(3)) + pose[9 + axis] for axis in range(3))


def compose(local, parent):
    basis = tuple(math.fsum(local[row * 3 + k] * parent[k * 3 + col] for k in range(3)) for row in range(3) for col in range(3))
    return (*basis, *point(local[9:12], parent), 1.0, 0.0, 0.0, 0.0)


def prism(document, edit):
    require(document.get("profile_kind", "polygon") == "polygon" and document.get("feature_kind", "blind_extrusion") == "blind_extrusion" and
            document["plane_axis"] == "z", "the first native prediction admits a corner-based Front-plane rectangular prism")
    vertices = document["vertices_m"]
    require(len(vertices) == 4 and vertices[0] == [0.0, 0.0], "the native prism prediction requires four corner-based vertices")
    width, height = vertices[1][0], vertices[2][1]
    require(vertices == [[0.0, 0.0], [width, 0.0], [width, height], [0.0, height]], "native prediction requires the ordered rectangle")
    depth = document["depth_m"] if edit is None else edit
    require(all(type(value) in (int, float) and math.isfinite(value) and value > 0 for value in (width, height, depth)), "native prism lengths must be positive finite values")
    return {"body_count": 1, "volume": width * height * depth, "area": 2 * (width * height + height * depth + width * depth),
            "com": [width / 2, height / 2, depth / 2],
            "dimensions_m": {"D1@Sketch1": width, "D2@Sketch1": height, "D1@Boss-Extrude1": depth}}


def predict(request):
    require(set(request) == {"bundle", "edit"} and set(request["edit"]) == {"part", "depth_m"}, "prediction requires a bundle and one independently authored depth edit")
    definitions = {row["id"]: row for row in request["bundle"]["definitions"]}
    require(len(definitions) == len(request["bundle"]["definitions"]) and request["bundle"]["root"] in definitions, "invalid prediction definition set")
    edit = request["edit"]
    require(edit["part"] in definitions and definitions[edit["part"]]["kind"] == "part" and
            edit["depth_m"] != definitions[edit["part"]]["request"]["document"]["depth_m"], "prediction requires an actual driving depth change")
    parts = {key: value for key, value in definitions.items() if value["kind"] == "part"}

    def tree(owner, edited):
        leaves = []
        total = 0

        def expand(key, world, ancestors):
            nonlocal total
            require(key not in ancestors and key in definitions, "prediction graph contains a cycle or missing definition")
            definition = definitions[key]
            if definition["kind"] == "part":
                depth = edit["depth_m"] if edited and key == edit["part"] else None
                shape = prism(definition["request"]["document"], depth)
                leaves.append(shape | {"com": point(shape["com"], world)})
                return []
            require(definition["kind"] == "assembly", "prediction requires a native part or assembly definition")
            rows = []
            for ordinal, item in enumerate(definition["occurrences"]):
                total += 1
                local = matrix(item["placement"])
                pose = compose(local, world)
                children = expand(item["target"], pose, ancestors | {key})
                rows.append({"ordinal": ordinal, "name": item["name"], "target": item["target"], "world": pose, "local": local, "children": children})
            return rows

        children = expand(owner, IDENTITY, set())
        volume = math.fsum(row["volume"] for row in leaves)
        require(volume > 0, "prediction requires visible solid leaf bodies")
        return {"children": children, "total_occurrences": total, "body_count": len(leaves), "volume": volume,
                "area": math.fsum(row["area"] for row in leaves), "com": [math.fsum(row["com"][axis] * row["volume"] for row in leaves) / volume for axis in range(3)]}

    result = {}
    for key, definition in definitions.items():
        native = definition["request"]
        path = PureWindowsPath(native["output"]["path_name"])
        config = native["document"]["configuration_name"] if key in parts else native["configuration_name"]
        original, edited = tree(key, False), tree(key, True)
        if key in parts:
            original.update(prism(native["document"], None))
            edited.update(prism(native["document"], edit["depth_m"] if key == edit["part"] else None))
        result[key] = {"kind": definition["kind"], "file": path.name, "configuration": config, "initial": original, "edited": edited}
    return {"schema": "kit.sw2026.generated-nested-prism-prediction.v1", "root": request["bundle"]["root"], "edit": edit, "definitions": result}


if __name__ == "__main__":
    print(json.dumps(predict(json.load(sys.stdin)), sort_keys=True, indent=2, allow_nan=False))
