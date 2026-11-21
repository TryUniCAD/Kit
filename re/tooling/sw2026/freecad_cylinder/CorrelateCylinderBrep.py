from collections import Counter
from hashlib import sha256
import json
from math import hypot, isclose, tau

from interchange.geometry.Models.Transform import Transform
from interchange.serialization.EncodeData import ToData


def require(value, reason):
    if not value:
        raise ValueError(reason)


def close(left, right):
    return isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)


def vector(value):
    return value["x"], value["y"], value["z"]


def axis(value):
    x, y, z = vector(value)
    return close(x, 0) and close(y, 0) and close(abs(z), 1)


def correlate(document, radius, height, body_id):
    if document.brep is None:
        return {"present": False, "status": "historical_projection_has_no_portable_brep",
                "new_kernel_identity_mapping_qualified": False}
    model = document.brep
    require(not model.validate(frozenset({body_id})), "source cylinder B-rep has invalid owned topology")
    encoded = ToData(model)
    rows = {name: value["$tuple"] for name, value in encoded.items()
            if isinstance(value, dict) and "$tuple" in value}
    counts = {name: len(items) for name, items in rows.items()}
    require(counts == {"bodies": 1, "coedges": 6, "curves": 3, "edges": 3, "face_uses": 3,
                       "faces": 3, "loops": 3, "pcurves": 0, "regions": 1, "shell_uses": 1,
                       "shells": 1, "surfaces": 3, "vertices": 2, "wires": 0},
            "source cylinder B-rep has an uncorrelated owner inventory")
    require(rows["bodies"][0]["design_body_id"] == body_id and rows["shells"][0]["closed"] is True,
            "source cylinder B-rep lost its actual body or closed shell")
    require(ToData(model.bodies[0].transform) == ToData(Transform()),
            "source cylinder B-rep has an additional body placement")
    surfaces = {row["id"]: row for row in rows["surfaces"]}
    cylinders = [row for row in rows["surfaces"] if row["$type"] == "CylinderSurface"]
    planes = [row for row in rows["surfaces"] if row["$type"] == "PlaneSurface"]
    require(len(cylinders) == 1 and len(planes) == 2, "source cylinder B-rep lacks its three analytic surfaces")
    cylinder = cylinders[0]
    require(close(cylinder["radius"], radius) and axis(cylinder["axis"])
            and all(close(value, 0) for value in vector(cylinder["origin"])),
            "source cylinder surface disagrees with the actual Radius or Placement")
    require(all(axis(row["normal"]) and close(row["origin"]["x"], 0)
                and close(row["origin"]["y"], 0) for row in planes)
            and all(close(observed, expected) for observed, expected in zip(
                sorted(row["origin"]["z"] for row in planes), (0.0, height), strict=True)),
            "source cylinder cap planes disagree with the actual Height or Placement")
    circles = [row for row in rows["curves"] if row["$type"] == "CircleCurve"]
    lines = [row for row in rows["curves"] if row["$type"] == "LineCurve"]
    require(len(circles) == 2 and len(lines) == 1
            and all(close(row["radius"], radius) and axis(row["axis"])
                    and close(row["center"]["x"], 0) and close(row["center"]["y"], 0) for row in circles)
            and all(close(observed, expected) for observed, expected in zip(
                sorted(row["center"]["z"] for row in circles), (0.0, height), strict=True)),
            "source cylinder rim curves disagree with the actual drivers")
    require(axis(lines[0]["direction"])
            and close(hypot(lines[0]["origin"]["x"], lines[0]["origin"]["y"]), radius),
            "source cylinder seam is not on the actual lateral radius")
    curves = {row["id"]: row for row in rows["curves"]}
    vertices = {row["id"]: row for row in rows["vertices"]}
    require(all(close(hypot(row["point"]["x"], row["point"]["y"]), radius) for row in rows["vertices"])
            and all(close(observed, expected) for observed, expected in zip(
                sorted(row["point"]["z"] for row in rows["vertices"]), (0.0, height), strict=True)),
            "source cylinder seam vertices disagree with the actual drivers")
    for edge in rows["edges"]:
        curve = curves[edge["curve_id"]]
        require(not edge["degenerate"], "source cylinder contains a degenerate edge")
        span = edge["end_parameter"] - edge["start_parameter"]
        if curve["$type"] == "CircleCurve":
            require(close(span, tau) and edge["start_vertex_id"] == edge["end_vertex_id"]
                    and close(vertices[edge["start_vertex_id"]]["point"]["z"], curve["center"]["z"]),
                    "source cylinder rim has a partial interval or a foreign endpoint")
        else:
            require(close(span, height)
                    and close(abs(vertices[edge["end_vertex_id"]]["point"]["z"]
                                  - vertices[edge["start_vertex_id"]]["point"]["z"]), height),
                    "source cylinder seam interval disagrees with its actual height")
    edge_uses = Counter(row["edge_id"] for row in rows["coedges"])
    require(set(edge_uses) == {row["id"] for row in rows["edges"]}
            and set(edge_uses.values()) == {2}, "source cylinder edge ownership is not paired")
    require({row["surface_id"] for row in rows["faces"]} == set(surfaces),
            "source cylinder has unused or duplicated face surfaces")
    digest = sha256(json.dumps(encoded, sort_keys=True, separators=(",", ":"),
                              ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    return {"present": True, "status": "retained_source_graph_with_analytic_owner_correlation",
            "source_graph_sha256": digest, "counts": counts,
            "side_face_ids": [row["id"] for row in rows["faces"] if row["surface_id"] == cylinder["id"]],
            "surface_owners": [{"face_id": row["id"], "same_sense": row["same_sense"],
                                "surface": surfaces[row["surface_id"]], "loop_ids": row["loop_ids"]["$tuple"]}
                               for row in rows["faces"]],
            "face_uses": rows["face_uses"], "new_kernel_identity_mapping_qualified": False,
            "whole_graph_native_equivalence_qualified": False,
            "new_native_construction_use": "excluded_until_full_source_mapping_is_qualified"}
