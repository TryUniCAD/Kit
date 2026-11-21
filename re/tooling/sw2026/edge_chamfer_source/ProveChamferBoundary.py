from argparse import ArgumentParser
from hashlib import sha256
from itertools import product
from math import hypot, isclose, prod, radians, tan
from pathlib import Path
from subprocess import run
import json
import sys

SCRIPT = Path(__file__).with_name("BuildChamferBoundary.py")
SOURCE_LOCK = "a696a97d73129ef7ffd7e829dfff7d1729000309e1273c0bef70b5f2ceedddb8"
PRIVATE_LOCK = "71523d573c97d6bb892556803b3c3914732664371b7e3292c54626b1fe2f7f43"


def digest(contents):
    return sha256(contents).hexdigest()


def read(path, sha):
    raw = path.read_bytes()
    assert digest(raw) == sha, "the frozen public source evidence differs"
    return json.loads(raw)


def readback(model, error=None):
    request = json.dumps(model, sort_keys=True, allow_nan=False).encode("utf-8")
    proc = run((sys.executable, "-I", "-B", str(SCRIPT)), input=request,
               capture_output=True, check=False, timeout=25)
    if error is not None:
        assert proc.returncode != 0 and not proc.stdout and error in proc.stderr.decode("utf-8")
        return error
    assert proc.returncode == 0 and not proc.stderr, proc.stderr.decode("utf-8")
    report = json.loads(proc.stdout)
    assert report["input_sha256"] == digest(request)
    assert report["runtime_access_attempts"] == report["native_file_outputs"] == 0
    return report


def equal(actual, prior):
    return isclose(actual, prior, rel_tol=7e-12, abs_tol=1e-16)


def same_basic(actual, expected):
    assert actual["counts"] == expected["counts"] == {"faces": 7, "edges": 15, "vertices": 10}
    assert len(actual["shell_ids"]) == 1 and actual["bevel_face_id"]
    assert all(equal(actual[key], expected[key]) for key in ("volume", "area"))
    assert len(actual["com"]) == 3 and all(equal(x, y) for x, y in zip(actual["com"], expected["com"], strict=True))


def disclosed(directory):
    lock = read(directory / "DisclosedSourceLock.json", SOURCE_LOCK)
    spec = read(directory / "Packet/Spec.json", lock["spec_sha256"])
    predicted = read(directory / "Packet/Predictions.json", lock["prediction_sha256"])
    assert lock["cohort"] == spec["cohort"] == "disclosed" and lock["passed"] and len(lock["sources"]) == 2
    results = []
    for locked in lock["sources"]:
        slot = locked["slot"]
        case, rows = spec["cases"][slot], predicted[slot]
        axis = rows["stock"]["edge_axis"]
        bounds, endpoint = (rows["stock"][key] for key in ("stock_bounds", "source_edge"))
        edge = endpoint[0]
        transverse = tuple(i for i in range(3) if i != axis)
        primary, relation = locked["orientation"]
        assert relation == "tan"
        for label in ("initial", "edited"):
            parameters = case if label == "initial" else case | case["edit"]
            model = {"body_id": f"disclosed/{slot}", "stock_bounds_m": bounds, "edge_axis": axis,
                     "corner": {str(i): bounds[i].index(edge[i]) for i in transverse},
                     "distance_axis": transverse[primary], "distance_m": parameters["distance_mm"] / 1000,
                     "angle_rad": radians(parameters["angle_deg"])}
            found, = [row["geometry"] for row in rows["states"][label] if row["branch"] == locked["orientation"]]
            report = readback(model)
            actual = report["kernel_neutral_topology"]
            same_basic(actual, found)
            assert all(any(all(equal(x, y) for x, y in zip(point, candidate, strict=True))
                           for candidate in actual["bevel_vertices_m"]) for point in found["bevel_vertices"])
            assert len(actual["bevel_vertices_m"]) == 4
            results.append({"slot": slot, "state": label, "geometry": actual, "model_sha256": report["input_sha256"],
                            "oracle_orientation_reproduced": True})
    return results


def synthetic():
    stock = [[-0.077, 0.043], [-0.018, 0.029], [0.012, 0.098]]
    widths = [b - a for a, b in stock]
    center = [(a + b) / 2 for a, b in stock]
    full = prod(widths)
    outputs = []
    for axis, bit_a, bit_b in product(range(3), range(2), range(2)):
        u, v = [i for i in range(3) if i != axis]
        a, b = .0049375, .0049375 * tan(.603125)
        depth, area_lost = widths[axis], a * b / 2
        volume_lost = depth * area_lost
        loss_center = list(center)
        loss_center[u] = stock[u][bit_a] + (1 - 2 * bit_a) * a / 3
        loss_center[v] = stock[v][bit_b] + (1 - 2 * bit_b) * b / 3
        expected = {"counts": {"faces": 7, "edges": 15, "vertices": 10}, "volume": full - volume_lost,
                    "area": 2 * (widths[u] * widths[v] - area_lost)
                    + depth * (2 * (widths[u] + widths[v]) - a - b + hypot(a, b)),
                    "com": [(full * value - volume_lost * missing) / (full - volume_lost)
                            for value, missing in zip(center, loss_center, strict=True)]}
        model = {"body_id": f"synthetic/{axis}-{bit_a}{bit_b}", "stock_bounds_m": stock, "edge_axis": axis,
                 "corner": {str(u): bit_a, str(v): bit_b}, "distance_axis": u, "distance_m": a, "angle_rad": .603125}
        actual = readback(model)
        same_basic(actual["kernel_neutral_topology"], expected)
        outputs.append({"axis": axis, "corner": [bit_a, bit_b], "model_sha256": actual["input_sha256"]})
    bad = {
        "zero_leg": (model | {"distance_m": 0}, "bevel must end inside both stock faces"),
        "through_stock": (model | {"distance_m": 0.27}, "bevel must end inside both stock faces"),
        "obtuse_angle": (model | {"angle_rad": 1.605}, "requires a positive acute angle"),
        "wrong_distance_axis": (model | {"distance_axis": model["edge_axis"]}, "one transverse stock side"),
        "unknown_corner": (model | {"corner": {"0": 2, "1": 0}}, "must name two actual stock extremes"),
        "flat_stock": (model | {"stock_bounds_m": [[0.0, 0.0], *stock[1:]]}, "requires positive extent"),
    }
    return outputs, {name: readback(item, expected) for name, (item, expected) in bad.items()}


if __name__ == "__main__":
    args = ArgumentParser()
    args.add_argument("disclosed", type=Path)
    options = args.parse_args()
    measured = disclosed(options.disclosed)
    others, refused = synthetic()
    assert len(measured) == 4 and len(others) == 12 and len(refused) == 6
    report = {"schema": "kit.sw2026.edge-chamfer-model-boundary.v1", "public_native_lock_sha256": SOURCE_LOCK,
              "prewriter_custody_receipt_sha256": PRIVATE_LOCK,
              "disclosed_states": measured, "independently_authored_cases": others,
              "refusals": refused, "guarded_processes": len(measured) + len(others) + len(refused),
              "runtime_access_attempts": 0, "native_file_outputs": 0, "heldout_writer_credit": 0,
              "constructor_sha256": digest(SCRIPT.read_bytes())}
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
