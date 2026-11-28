from argparse import ArgumentParser
from hashlib import sha256
from math import isclose
from pathlib import Path, PureWindowsPath
from subprocess import run
import json
import os
import sys


def digest(data):
    return sha256(data).hexdigest()


def require(value, detail):
    if not value:
        raise ValueError(detail)


def number(actual, expected):
    require(isclose(float(actual), float(expected), rel_tol=1e-11, abs_tol=1e-9),
            f"native read value differs: {actual} versus {expected}")


def worker(root):
    sys.path[:0] = [str(root / "src"), str(root)]
    from convert import open_document
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from interchange.geometry.Models.GeometryCurves import CircleGeometry, PointGeometry

    request = json.load(sys.stdin)
    path = Path(request["path"])
    payload = path.read_bytes()
    require(digest(payload) == request["sha256"], "immutable reader input changed")
    observed_exec = []

    def reject_process(event, args):
        if event in ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn"):
            observed_exec.append(event)
            raise PermissionError("reader cannot start an application or native tool")

    sys.addaudithook(reject_process)
    document = open_document(path, include_brep=False, include_tessellation=False)
    require(not document.validate() and len(document.bodies) == 1, "opened model does not validate")
    evidence = document.metadata["solidworks.typed_resolved_semantics"]
    require(evidence["status"] == "supplemented" and len(evidence["circle_profiles"]) == 1,
            "actual circle and end graph did not reach the public reader")
    (sketch,) = document.sketches
    circular = [entity for entity in sketch.entities if type(entity.geometry) is CircleGeometry]
    points = [entity for entity in sketch.entities if type(entity.geometry) is PointGeometry]
    require(len(circular) == len(points) == 1 and len(sketch.entities) == 2, "circle or actual centre is missing")
    circle, center = circular[0], points[0]
    radial, fixed = sketch.constraints
    require(radial.kind == request["mode"] and radial.driving and len(radial.references) == 1 and
            radial.references[0].entity_id == circle.id and fixed.kind == "fixed" and
            len(fixed.references) == 1 and fixed.references[0].entity_id == center.id and
            sketch.closed_profile_entity_ids == ((circle.id,),) and sketch.parameter_ids == (radial.parameter_id,),
            "public loop or either relation lost its native owner")
    shape = circle.geometry
    for actual, expected in zip((shape.center.x, shape.center.y), request["center_mm"], strict=True):
        number(actual, expected)
    require(center.geometry.point == shape.center, "fixed point is not the actual circle centre")
    number(shape.radius, request["radius_mm"])
    p = document.parameter(radial.parameter_id)
    require(p.name == "D1" and p.role == "driving" and p.value.unit == "mm" and
            p.attributes["typed_archive_owner"]["value_field"] == "f58",
            "public radial parameter lost its actual length owner")
    number(p.value.value, request["radius_mm"] * (2 if request["mode"] == "diameter" else 1))
    plane = next(value for value in document.support_planes if value.id == sketch.support_plane_id)
    axis = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[request["axis"]]
    normal = plane.transform.z_axis
    require((normal.x, normal.y, normal.z) == axis, "circle support normal changed")
    (feature,) = [value for value in document.feature_timeline if value.name == request["feature"]]
    definition = feature.definition
    expected_mode = {"blind": "blind", "mid_plane": "mid_plane", "two_directions": "two_lengths"}[request["end_condition"]]
    require(feature.sketch_id == sketch.id and definition.end_condition == expected_mode and
            definition.reversed is request["reverse"] and definition.symmetric is (expected_mode == "mid_plane"),
            "typed reversal, midpoint or actual sketch ownership changed")
    number(definition.length.value, request["depth_mm"])
    native_depths = {"D1": (request["depth_mm"], "f818.f18")}
    second = request["second_mm"]
    if second is None:
        require(definition.second_length is None and definition.second_end_condition is None, "single end acquired a second active length")
    else:
        require(definition.second_end_condition == "blind", "second active end lost its type")
        number(definition.second_length.value, second)
        native_depths["D2"] = second, "f818.f20"
    parameters = {p.name: p for p in document.parameters if p.owner_id == feature.id}
    require(set(parameters) == set(native_depths), "unexpected active extrusion dimension")
    for name, (length, slot) in native_depths.items():
        value = parameters[name]
        require(value.role == "driving" and value.value.unit == "mm" and
                value.attributes["typed_archive_owner"]["slot"] == slot and value.id in feature.parameter_ids,
                "extrusion driver is no longer bound to its end slot")
        number(value.value.value, length)
    archive = SldprtArchive.from_bytes(payload)
    link = ReadNativeLink(archive, 0)
    resolved = link.ResolvedValue
    emitted = WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000,
                            link.ConfigValue.MapValue, resolved.ContextValue)[0]
    require(emitted == archive.require(link.StreamName), "typed resolved round trip changed bytes")
    config = link.ConfigValue
    require(WriteConfigMut(config.RootValue, 19000, config.HeaderValue)[0] == archive.require(link.ConfigName),
            "typed configuration round trip changed bytes")
    require(digest(path.read_bytes()) == request["sha256"] and not observed_exec, "reader crossed input or runtime custody")
    return {"pid": os.getpid(), "case": request["case"], "phase": request["phase"],
            "file_sha256": request["sha256"], "end_condition": expected_mode, "reverse": definition.reversed,
            "owned_depths": {name: parameters[name].value.value for name in parameters},
            "radial_mode": radial.kind, "radial_mm": p.value.value, "typed_streams_exact": 2, "passed": True}


def requests(packet, job, inspection):
    for case, observed in zip(job["cases"], inspection["cases"], strict=True):
        shape = case["request"]["document"]
        guest_source = Path(case["path"])
        case_name = case["name"]
        require(observed["name"] == case_name and observed["passed"], "native lifecycle did not pass")
        after_edit = observed["phases"][2]
        initial_save = observed["phases"][0]
        for phase, path, identity, radial, depth, second in (
            ("generated", packet / guest_source.parent.name / guest_source.name,
             case["sha256"], 1.0, 1.0, 1.0),
            ("first-save", packet / "Inspection" / case_name / initial_save["phase"] /
             PureWindowsPath(initial_save["saved_path"]).name, initial_save["saved_sha256"], 1.0, 1.0, 1.0),
            ("edited-fresh-reopen", packet / "Inspection" / case_name / after_edit["phase"] /
             PureWindowsPath(after_edit["saved_path"]).name, after_edit["saved_sha256"],
             case["edit_factor"], case["depth_edit_factor"], case.get("reverse_depth_edit_factor", 1.0)),
        ):
            yield {
                "path": str(path), "sha256": identity, "case": case_name, "phase": phase,
                "axis": shape["plane_axis"], "feature": shape["extrusion_name"],
                "mode": shape["circle_dimension"]["mode"], "center_mm": [k * 1000 for k in shape["center_m"]],
                "radius_mm": shape["radius_m"] * radial * 1000, "depth_mm": shape["depth_m"] * depth * 1000,
                "second_mm": None if "reverse_depth_m" not in shape else shape["reverse_depth_m"] * second * 1000,
                "reverse": shape["reverse_direction"], "end_condition": shape["end_condition"],
            }


def main():
    parser = ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("packet", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--native-sha256", required=True)
    args = parser.parse_args()
    job = (args.packet / "InspectionJob.json").read_bytes()
    result = (args.packet / "Inspection" / "Inspection.json").read_bytes()
    require(digest(job) == args.packet_sha256 and digest(result) == args.native_sha256, "native job or result differs")
    decoded = json.loads(result)
    require(decoded["passed"] and decoded["controls_healthy"] and decoded["job_sha256"] == args.packet_sha256,
            "native lifecycle or controls did not qualify")
    rows = []
    for sample in requests(args.packet, json.loads(job), decoded):
        call = [sys.executable, "-I", "-B", str(Path(__file__).resolve()), "worker", str(args.root.resolve())]
        answer = run(call, input=json.dumps(sample).encode(), capture_output=True, check=False)
        require(answer.returncode == 0, answer.stderr.decode(errors="replace"))
        rows.append(json.loads(answer.stdout))
    require(len(rows) == len({row["pid"] for row in rows}) == 12 and all(row["passed"] for row in rows),
            "all three states require separate verified reader processes")
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump({"passed": True, "native_job_sha256": args.packet_sha256,
                   "native_result_sha256": args.native_sha256, "records": rows},
                  handle, sort_keys=True, indent=2)
        handle.write("\n")
    print(digest(args.output.read_bytes()))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "worker":
        print(json.dumps(worker(Path(sys.argv[2])), sort_keys=True))
    else:
        main()
