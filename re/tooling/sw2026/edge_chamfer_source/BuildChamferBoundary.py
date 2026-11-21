from codecs import lookup
from hashlib import sha256
from itertools import product
from math import fsum, isfinite, pi, tan
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit


def require(check, message):
    if not check:
        raise ValueError(message)


def component(value):
    require(type(value) in (int, float) and isfinite(value), "edge and stock coordinates must be finite")
    return float(value)


def safe_pair(values):
    require(isinstance(values, list) and len(values) == 2, "each stock axis requires two bounds")
    bounds = tuple(component(value) for value in values)
    require(bounds[0] < bounds[1], "each stock axis requires positive extent")
    return bounds


def unit(axis):
    return SpaceVector(*(float(n == axis) for n in range(3)))


def corner_ring(bounds, axes, bits, legs):
    x, y = axes
    sizes = {axis: bounds[axis][1] - bounds[axis][0] for axis in axes}
    require(all(0 < legs[axis] < sizes[axis] for axis in axes), "the bevel must end inside both stock faces")
    box = tuple((bounds[x][i], bounds[y][j]) for i, j in ((0, 0), (1, 0), (1, 1), (0, 1)))
    corner = tuple(bounds[axis][bits[axis]] for axis in axes)
    index = box.index(corner)
    clipped = []
    for side in (box[index - 1], box[(index + 1) % len(box)]):
        point = tuple(
            start + (end - start) * (legs[axis] / sizes[axis])
            for axis, start, end in zip(axes, corner, side, strict=True)
        )
        clipped.append(point)
    return (*box[:index], *clipped, *box[index + 1:]), tuple(clipped)


def centroid(ring):
    first_x, first_y = ring[0]
    local = tuple((x - first_x, y - first_y) for x, y in ring)
    sides = tuple(zip(local, local[1:] + local[:1], strict=True))
    wedges = tuple(x * ny - y * nx for (x, y), (nx, ny) in sides)
    twice = fsum(wedges)
    require(twice > 0 and isfinite(twice), "edge bevel footprint must have positive oriented area")
    return (
        first_x + fsum((x + nx) * w for ((x, _), (nx, _)), w in zip(sides, wedges, strict=True)) / (3 * twice),
        first_y + fsum((y + ny) * w for ((_, y), (_, ny)), w in zip(sides, wedges, strict=True)) / (3 * twice),
    )


def boundary(model):
    require(set(model) == {"body_id", "stock_bounds_m", "edge_axis", "corner", "distance_axis", "distance_m", "angle_rad"},
            "edge bevel requires explicit stock, selected edge, and distance-side orientation")
    require(type(model["body_id"]) is str and bool(model["body_id"]), "edge bevel needs a modeled body identity")
    require(type(model["stock_bounds_m"]) is list and len(model["stock_bounds_m"]) == 3,
            "edge bevel needs three independent stock axes")
    bounds = tuple(safe_pair(values) for values in model["stock_bounds_m"])
    axis = model["edge_axis"]
    primary = model["distance_axis"]
    require(type(axis) is int and type(primary) is int and 0 <= axis < 3 and 0 <= primary < 3 and axis != primary,
            "distance must be assigned to one transverse stock side")
    axes = ((axis + 1) % 3, (axis + 2) % 3)
    secondary = next(index for index in axes if index != primary)
    raw_corner = model["corner"]
    require(isinstance(raw_corner, dict) and set(raw_corner) == {str(i) for i in axes}
            and all(type(value) is int and value in (0, 1) for value in raw_corner.values()),
            "selected edge must name two actual stock extremes")
    bits = {key: raw_corner[str(key)] for key in axes}
    distance, theta = (component(model[key]) for key in ("distance_m", "angle_rad"))
    require(0 < theta < pi / 2, "edge bevel requires a positive acute angle")
    legs = {primary: distance, secondary: distance * tan(theta)}
    ring, clip = corner_ring(bounds, axes, bits, legs)
    vertex_ring = tuple(PlaneVector(x * 1000, y * 1000) for x, y in ring)
    lines = tuple(LineGeometry(x, y) for x, y in zip(vertex_ring, vertex_ring[1:] + vertex_ring[:1], strict=True))
    origin = SpaceVector(*(1000 * bounds[axis][0] if i == axis else 0.0 for i in range(3)))
    frame = Transform(origin, unit(axes[0]), unit(axes[1]), unit(axis))
    depth = bounds[axis][1] - bounds[axis][0]
    body, volume, area, box = BuildPrism(model["body_id"], frame, lines, 0.0, depth * 1000)

    def map_point(pos, station):
        vector = {axes[0]: pos[0], axes[1]: pos[1], axis: station}
        return [vector[i] for i in range(3)]

    com = map_point(centroid(ring), bounds[axis][0] + depth / 2)
    new_points = tuple(map_point(pos, end) for pos, end in product(clip, bounds[axis]))
    side_index = next(index for index, source in enumerate(ring) if source == clip[0])
    return body, {"volume": volume * 1e-9, "area": area * 1e-6, "com": com, "bevel_vertices_m": new_points,
                  "bounds_m": [[getattr(vector, k) * 0.001 for k in "xyz"] for vector in (box.minimum, box.maximum)],
                  "bevel_face_id": body.faces[side_index + 2].id,
                  "counts": {"faces": len(body.faces), "edges": len(body.edges), "vertices": len(body.vertices)},
                  "shell_ids": [shell.id for shell in body.shells]}


def run():
    tuple(lookup(codec) for codec in ("utf-8", "ascii", "utf-16-le", "latin-1"))
    raw = sys.stdin.buffer.read()
    model = json.loads(raw)
    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    sys.addaudithook(audit.InspectEvent)
    audit.BeginBuild()
    body, values = boundary(model)
    require(len(body.bodies) == len(body.shells) == 1 and values["counts"] == {"faces": 7, "edges": 15, "vertices": 10},
            "edge bevel must produce one actual five-sided prism topology")
    require(not audit.DeniedReads, "edge-bevel boundary used external input or a CAD process")
    return {"input_sha256": sha256(raw).hexdigest(), "kernel_neutral_topology": values,
            "runtime_access_attempts": 0, "native_file_outputs": 0}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True, allow_nan=False))
