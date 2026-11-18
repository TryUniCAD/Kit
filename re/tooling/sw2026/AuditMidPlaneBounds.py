from argparse import ArgumentParser
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(root), str(root / "src")]

from convert import open_document
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature


def coords(point):
    return (point.x, point.y, point.z)


def vertex_bounds(model):
    points = tuple(coords(value.point) for value in model.vertices)
    return tuple(tuple(fn(point[axis] for point in points) for axis in range(3))
                 for fn in (min, max))


def equal(first, second):
    return all(isclose(a, b, rel_tol=1e-10, abs_tol=1e-10)
               for first_corner, second_corner in zip(first, second, strict=True)
               for a, b in zip(first_corner, second_corner, strict=True))


def main():
    parser = ArgumentParser(description="Compare parametric stock bounds with the active saved solid")
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--capture-baseline", action="store_true")
    args = parser.parse_args()
    cases = []
    for folder, name, axis, digest in (
        ("GeneratedThroughAll02", "ThroughAllD01CutForward", 2, "ced6b5c0e3ab5593c40ee776f50c68972c63b2599e49598be01d4786bffaa63d"),
        ("GeneratedThroughAllReverse01", "ThroughAllD02CutReverse", 1, "e342763ba76cd09fc21a4f777127d0ff442b3c4b637acefecf1a974fbaf52431"),
        ("GeneratedThroughAllBoth01", "ThroughAllD03CutBoth", 0, "cc4ec3d3d0d337186a83338eada5d16c73d041aec73962beb3ce0be852c19712"),
    ):
        path = args.sources / folder / "Control" / (name + ".SLDPRT")
        raw = path.read_bytes()
        assert sha256(raw).hexdigest() == digest
        kernel = open_document(raw, source_format="solidworks.sldprt", include_tessellation=False)
        assert not kernel.validate() and kernel.brep is not None and kernel.brep_payloads
        expected = vertex_bounds(kernel.brep)
        checks = []
        for payload in (path, raw):
            doc = open_document(payload, source_format="solidworks.sldprt", include_brep=False,
                                include_tessellation=False)
            assert not doc.validate() and doc.brep is None and not doc.brep_payloads
            (body,) = doc.bodies
            (stock,) = tuple(value.definition for value in doc.feature_timeline
                             if isinstance(value.definition, ExtrudeFeature)
                             and value.definition.end_condition == ExtrudeEnd.KMidPlane)
            box = body.topology.bounding_box
            assert stock.length is not None and box is not None
            actual = coords(box.minimum), coords(box.maximum)
            radius = stock.length.value / 2
            assert isclose(expected[0][axis], -radius, rel_tol=1e-10, abs_tol=1e-10)
            assert isclose(expected[1][axis], radius, rel_tol=1e-10, abs_tol=1e-10)
            matches = equal(actual, expected)
            assert matches != args.capture_baseline, (name, actual, expected)
            if args.capture_baseline:
                assert isclose(actual[0][axis], 0.0, abs_tol=1e-10) or isclose(actual[1][axis], 0.0, abs_tol=1e-10)
            checks.append((actual, matches))
        assert checks[0] == checks[1]
        cases.append({"name":name,"source_sha256":digest,"station_axis":"xyz"[axis],
                      "typed_solid_bounds_mm":expected,"parametric_bounds_mm":checks[0][0],
                      "stock_bounds_match":checks[0][1],"path_and_bytes_equal":True})
    report = {"schema":"kit.sw2026.mid-plane-stock-bounds.v1","passed":True,
              "expected_legacy_miss":args.capture_baseline,"method_sha256":sha256(Path(__file__).read_bytes()).hexdigest(),
              "native_launches":0,"hidden_inputs_read":0,"cases":cases,"disabled_geometry_reads":2 * len(cases)}
    raw = (json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+"\n").encode()
    with args.output.open("xb") as file:
        file.write(raw)
    print(json.dumps({"passed":True,"reads":report["disabled_geometry_reads"],"result_sha256":sha256(raw).hexdigest()}))


if __name__ == "__main__":
    main()
