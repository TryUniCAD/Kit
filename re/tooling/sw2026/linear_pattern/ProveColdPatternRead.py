from argparse import ArgumentParser
from collections import Counter
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from math import isclose
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
import json
import sys


TOOL = Path(__file__).resolve()
ROOT = TOOL.parents[4]
MEASUREMENTS = ROOT / "re/solidworks/measurements/2026"
FORMAT = "solidworks.sldprt"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def summary(doc):
    from interchange.Features.FeatureKinds import LinearPattern

    require(not doc.validate(), "strict read contains invalid neutral owners")
    feature, = [row for row in doc.feature_timeline if isinstance(row.definition, LinearPattern)]
    body, = doc.bodies
    model = doc.brep
    require(model is not None and not doc.brep_payloads and model.bodies[0].design_body_id == body.id
            and body.final_feature_id == feature.id, "derived solid lost its actual pattern or created a cache")
    state = doc.metadata["solidworks.typed_linear_pattern"]
    require(state["status"] == "projected_cold_single_direction" and state["physical_body_node"] is None
            and state["public_writer_qualified"] is False and body.attributes["solidworks.native_kernel_identity"] is False,
            "cache-free body claims a persisted kernel identity or writer capability")
    edges = Counter((use.edge_id, use.reversed) for use in model.coedges)
    require(len(model.bodies) == len(model.shells) == 1 and model.shells[0].closed
            and len(edges) == 2 * len(model.edges) and all(count == 1 for count in edges.values())
            and all(edges[(edge.id, False)] == edges[(edge.id, True)] == 1 for edge in model.edges),
            "derived shell contains a missing or same-direction paired edge use")
    holes = [loop.id for loop in model.loops if loop.outer is False]
    require(len(holes) == feature.definition.instance_count
            and sum(set(holes).issubset(row.loop_ids) for row in model.faces) == 1,
            "translated profiles failed to share one physical upper plate face")
    feature_names = {row.id: row.name for row in doc.feature_timeline}
    datum_step = next(row for row in doc.feature_timeline if row.id == feature.input_feature_ids[1])
    angle, = [value for value in doc.parameters if value.owner_id == datum_step.id and value.value.kind.value == "angle"]
    require(angle.role.value == "driving" and angle.value.unit == "rad", "local datum angle lost its actual driving value")
    params = [row for row in doc.parameters if row.owner_id == feature.id]
    require([row.name for row in params] == ["D1", "D3"]
            and all(row.role.value == "driving" for row in params),
            "pattern drivers lost count or pitch ownership")
    bounds = body.topology.bounding_box
    require(bounds is not None and body.topology.valid is True, "derived body lost its exact bounds")
    box = tuple(getattr(point, axis) for point in (bounds.minimum, bounds.maximum) for axis in "xyz")
    return {
        "configuration": doc.configurations[0].name,
        "body_count": body.topology.solid_count, "face_count": body.topology.face_count,
        "edge_count": body.topology.edge_count, "vertex_count": body.topology.vertex_count,
        "bounds_mm": box, "centroid_mm": body.attributes["solidworks.body_centroid_mm"],
        "volume_mm3": body.topology.volume, "area_mm2": body.topology.surface_area,
        "count": feature.definition.instance_count, "pitch_mm": feature.definition.spacing.value,
        "reversed": feature.definition.reversed, "angle_rad": angle.value.value,
        "parents": [feature_names[key] for key in feature.input_feature_ids],
        "atoms": state["native_atom_lineage"], "kernel_payload_count": len(doc.brep_payloads),
    }


def read_worker(input_path=None):
    sys.path.insert(0, str(ROOT / "src"))
    from convert import open_document
    from convert.adapters.base.ReadOptions import ReadOptions
    from convert import registry

    raw = sys.stdin.buffer.read()

    def deny_launch(event, args):
        require(event not in ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn"),
                "normal reader attempted an external CAD process")

    sys.addaudithook(deny_launch)
    report = summary(open_document(BytesIO(raw), source_format=FORMAT, strict=True))
    if input_path is not None:
        require(summary(open_document(input_path, strict=True)) == report,
                "native path and stream reading disagree")
    raw_doc = registry.read(raw, format_id=FORMAT, options=ReadOptions(extract_raw_brep=True, include_brep=False))
    require(raw_doc.brep is None and "solidworks.typed_linear_pattern" not in raw_doc.metadata,
            "metadata-only reader constructed a solid")
    require(not any(name in ("Swapp", "pythoncom", "pywintypes") or name.startswith("win32com") for name in sys.modules),
            "application library loaded in cache-free read")
    sys.stdout.buffer.write(encode(report))


def compare(report, fixture, request):
    geometry = fixture["analytic_geometry"]
    expected = {
        "bounds_mm": [value * 1000 for value in geometry["bounds_m"]],
        "centroid_mm": [value * 1000 for value in geometry["centroid_m"]],
        "volume_mm3": geometry["volume_m3"] * 1e9,
        "area_mm2": geometry["area_m2"] * 1e6,
    }
    expected_counts = {
        "configuration": request["seed"]["configuration"],
        "body_count": geometry["body_count"], "face_count": geometry["face_count"],
        "edge_count": 12 * (request["pattern"]["count"] + 1),
        "vertex_count": 8 * (request["pattern"]["count"] + 1),
        "count": request["pattern"]["count"], "pitch_mm": request["pattern"]["pitch_m"] * 1000.0,
        "reversed": request["pattern"]["reverse"], "angle_rad": request["plane"]["angle_rad"],
        "parents": [request["seed"]["seed"]["feature"], request["plane"]["name"]],
        "atoms": [101, 102, 103], "kernel_payload_count": 0,
    }
    require(all(report[key] == value for key, value in expected_counts.items()),
            "reconstructed root, sketch ownership, count or explicit configuration differs")
    for key, value in expected.items():
        stored, match = ((report[key], value) if isinstance(value, list) else ((report[key],), (value,)))
        require(all(isclose(actual, measured, rel_tol=1e-12, abs_tol=1e-11)
                    for actual, measured in zip(stored, match, strict=True)),
                "computed solid differs from independent occupied cells")


def measure(exact_hashes):
    fields = json.loads((MEASUREMENTS / "LocalLinearPatternContainer01.json").read_bytes())["model_cases"]
    receipts = json.loads((MEASUREMENTS / "LocalLinearPatternNeutralInput01.json").read_bytes())["cases"]
    results = {}
    with TemporaryDirectory(prefix="KitColdPattern.") as tmp:
        for name, states in fields.items():
            result = {}
            for state, case in states.items():
                request = case["modeled_input"]
                compile_tool = TOOL.with_name("LocalPatternContainerProcess.py")
                compiled = run([sys.executable, "-I", "-B", str(compile_tool), "--binary"],
                               input=encode(request), capture_output=True, check=False, cwd=ROOT, timeout=60)
                require(compiled.returncode == 0 and not compiled.stderr, compiled.stderr.decode())
                digest = sha256(compiled.stdout).hexdigest()
                if exact_hashes:
                    require(digest == receipts[name][state]["native_container"]["sha256"],
                            "generated part changed from the independently proven model hash")
                target = Path(tmp) / (name + state + ".SLDPRT")
                target.write_bytes(compiled.stdout)
                checked = run([sys.executable, "-I", "-B", str(TOOL), "--worker", str(target)],
                              input=compiled.stdout, capture_output=True, check=False, cwd=ROOT, timeout=60)
                require(checked.returncode == 0 and not checked.stderr, checked.stderr.decode())
                row = json.loads(checked.stdout)
                compare(row, receipts[name][state], request)
                result[state] = {"source_sha256": digest, **row}
            results[name] = result
    require(len(results) == 2 and all(len(value) == 3 for value in results.values()), "incomplete pattern contrast")
    return {"schema": "kit.sw2026.public-cold-oblique-pattern-read.v1", "cases": results, "isolated_processes": 12,
            "ordinary_path_and_stream_reads": 12, "exact_generated_hashes_required": exact_hashes,
            "heldout_payloads_read": 0, "native_processes_started": 0}


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--portable", action="store_true")
    args = parser.parse_args()
    if args.worker is not None:
        read_worker(args.worker)
        return
    data = encode(measure(not args.portable))
    if args.output is None:
        sys.stdout.buffer.write(data)
    else:
        with args.output.open("xb") as stream:
            stream.write(data)
        print(sha256(data).hexdigest())


if __name__ == "__main__":
    main()
