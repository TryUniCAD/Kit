from argparse import ArgumentParser
from datetime import datetime, timezone
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from json import dumps, load, loads
from pathlib import Path, PureWindowsPath
from struct import pack, unpack_from
from subprocess import run
from types import FunctionType
import sys


PACKET_SHA = "8f38fd02f84cd554342005cd2dd0457de879cd443e96d2721af05d770cbb0bdd"
NATIVE_SHA = "e94dd631acd5942a53296f36b77d1c3bc8b321e8ba7fd725327c74ac4a12916c"
PRIOR_SHA = "35fa6556f82f7312cceeb8ba689416ce8d36de7be185de795c54a1e1a67973a5"
SOURCE_SHA = "c1499c173a495b0186e3acf733fcfb02b7bdb94fc46a6a902768fedec44d0e72"
WORKER_FILE = "re/tooling/sw2026/CheckSdkCircleRead.py"
WORKER_SHA = "d0f92416cf7aaec2abc773b3923e685fb117bbb594563b8fdba7375b04fc4ef3"
OLD_CENTRE_CHECK = "fixed point is not the actual circle centre"
UNVERIFIED = ("full document metadata and assigned material", "appearance, drawings and assemblies",
              "public writer registration", "unrelated solver, feature and geometry families")


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def digest(data):
    return sha256(data).hexdigest()


def exact_bytes(path, identity):
    value = path.read_bytes()
    require(digest(value) == identity, "immutable input hash differs: " + path.name)
    return value


def exact_json(path, identity):
    return loads(exact_bytes(path, identity))


def save(path, value):
    data = (dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with path.open("xb") as sink:
        sink.write(data)
    return digest(data)


def verified_workspace(workspace):
    packet = exact_json(workspace / "Packet/Packet.json", PACKET_SHA)
    native = exact_json(workspace / "Packet/Inspection/Result.json", NATIVE_SHA)
    prior = exact_json(workspace / "Readback.json", PRIOR_SHA)
    original = exact_json(workspace / "GeneratedFreeze.json", packet["generated_freeze_sha256"])
    method = exact_json(workspace / "Method.json", original["method_sha256"])
    source = exact_json(workspace / "SDK/FrozenSource.json", SOURCE_SHA)
    require(packet["reader_source_manifest_sha256"] == packet["writer_source_manifest_sha256"] ==
            method["sdk"]["manifest_sha256"] == SOURCE_SHA and
            source["file_count"] == len(source["files_sha256"]) == 5017 and
            source["files_sha256"][WORKER_FILE] == WORKER_SHA, "the exact SDK reader closure differs")
    sdk = workspace / "SDK/Kit"
    for relative, identity in source["files_sha256"].items():
        path = sdk / relative
        require(not path.is_symlink() and path.resolve(strict=True).is_relative_to(sdk), "source escapes the frozen SDK")
        exact_bytes(path, identity)
    require(native["packet_sha256"] == prior["packet_sha256"] == PACKET_SHA and
            prior["native_sha256"] == NATIVE_SHA and native["passed"] and native["inputs_immutable"] and
            native["controls_healthy"] and native["distinct_processes"] == native["native_processes"] == 14 and
            len(native["controls"]) == 2 and all(row["healthy"] for row in native["controls"]) and
            prior["passed"] is False and prior["typed_streams_exact"] == 20 and len(prior["readbacks"]) == 10,
            "the native qualification or prior partial readback differs")
    for name, identity in packet["tools_sha256"].items():
        exact_bytes(workspace / "Packet/Tools" / name, identity)
    for relative, identity in packet["files_sha256"].items():
        exact_bytes(workspace / "Packet" / relative, identity)
    failures = {(row["case"], row["phase"]) for row in prior["unsupported_inputs_or_owners"]}
    require(failures == {("H03MidPlaneGenerated", "first-save"), ("H03MidPlaneGenerated", "edited-fresh-reopen-save")} and
            all(OLD_CENTRE_CHECK in row["reason"] for row in prior["unsupported_inputs_or_owners"]),
            "the original failure remains specifically the centre predicate")
    return sdk, packet, native, prior, source


def measured_inputs(workspace, packet, native):
    base = workspace / "Packet"
    names = ("H03MidPlane", "H04TwoDirections")
    require(tuple(row["name"] for row in packet["cases"]) == tuple(row["name"] for row in native["cases"]) == names,
            "the measured cohort differs")
    for case, case_result in zip(packet["cases"], native["cases"], strict=True):
        spec = case["spec"]
        for lane, suffix, folder in (("reference", "Reference", "Original"), ("generated", "Generated", "Generated")):
            label = case["name"] + suffix
            phases = case_result["lanes"][lane]
            origin = base / case["name"] / folder / PureWindowsPath(case[lane + "_path"]).name
            identity = case[lane + "_sha256"]
            require(tuple(row["phase"] for row in phases) == ("open-save", "fresh-reopen", "edited-fresh-reopen") and
                    all(row["passed"] and row["source_immutable"] for row in phases) and
                    [row["source_sha256"] for row in phases] == [identity, phases[0]["saved_sha256"], phases[1]["saved_sha256"]],
                    "the native saved chain differs")
            edit = (case["edit_factor"], case["depth_edit_factor"], case.get("reverse_depth_edit_factor", 1.0))
            inputs = [("input", origin, identity, (1.0, 1.0, 1.0))]
            for phase, tag, factors in ((phases[0], "first-save", (1.0, 1.0, 1.0)),
                                        (phases[2], "edited-fresh-reopen-save", edit)):
                basename = PureWindowsPath(phase["saved_path"]).name
                require(basename == label + "Saved.SLDPRT", "the native saved name differs")
                inputs.append((tag, base / "Inspection" / label / phase["phase"] / basename, phase["saved_sha256"], factors))
            for tag, path, checksum, (radius, depth, second) in inputs:
                require(not path.is_symlink() and path.resolve(strict=True).is_relative_to(base), "reader input escapes packet")
                yield {"path": str(path), "sha256": checksum, "case": label, "phase": tag,
                       "axis": {"right": "x", "top": "y"}[spec["plane"]], "feature": spec["feature_name"],
                       "sketch": spec["sketch_name"], "mode": spec["mode"], "center_mm": spec["center_mm"],
                       "radius_mm": spec["radius_mm"] * radius, "depth_mm": spec["depth_mm"] * depth,
                       "second_mm": None if spec["second_mm"] is None else spec["second_mm"] * second,
                       "reverse": spec["reverse"], "end_condition": spec["end_condition"]}


def pair(vector):
    return (vector.x, vector.y)


def bits(coordinates):
    return pack("<2d", *coordinates)


def marker_millimetres(metres):
    projected = (round(x * 1000.0, 12) for x in metres)
    return tuple(0.0 if abs(x) <= 1e-12 else x for x in projected)


def projected_point(point, circle, native_sketch, center, sketch_id, stream_name, stream, metres):
    from convert.adapters.solidworks.Core.Native import KMarkers, MarkerMetres

    span, = point.provenance.spans
    require(span.stream == stream_name and native_sketch.StartOffset <= span.offset and
            span.offset + span.length <= native_sketch.EndOffset, "the public centre escapes its actual linked sketch")
    if span.record_kind == "typed-archive-object":
        require(span.offset == native_sketch.StartOffset and span.offset + span.length == native_sketch.EndOffset and
                point.id == f"sldprt:sketch:{sketch_id}:point:{center['f0c']}" and
                point.attributes["native_permanent_mark"] == center["f0c"] and
                circle.provenance.spans == (span,), "the typed public centre lacks its real native mark")
        return {"route": "typed-centre", "expected_mm": tuple(x * 1000.0 for x in metres)}
    offset = span.offset
    require(offset - 4 >= native_sketch.StartOffset, "the saved point marker has no linked identity word")
    marker_index = unpack_from("<I", stream, offset - 4)[0]
    require(span.record_kind == "sketch-native-marker" and
            point.id == f"sldprt:sketch:{sketch_id}:native:{offset}" and point.provenance.native_id == f"{sketch_id}:{offset}" and
            point.attributes["semantic"] == "point" and
            any(stream.startswith(prefix, offset) for prefix in KMarkers) and
            marker_index == point.attributes["object_index"] == center["f0c"],
            "the saved point marker does not identify the centre row")
    marker_metres = MarkerMetres(stream, offset, offset + span.length)
    require(marker_metres is not None and bits(marker_metres) == bits(metres),
            "the actual saved marker metres differ from the shared typed centre's raw coordinates")
    return {"route": "saved-point-marker", "marker_offset": offset, "marker_object_index": marker_index,
            "marker_metres_hex": [x.hex() for x in marker_metres],
            "expected_mm": marker_millimetres(marker_metres)}


def prove_shared_centre(request):
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
    from convert.adapters.solidworks.Core.TypedResolved.ReadCircleShape import ReadCircleShape
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
    from convert.adapters.solidworks.Core.TypedResolved.ReadRadialDrive import ReadRadialDrive
    from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
    from interchange.geometry.Models.GeometryCurves import CircleGeometry, PointGeometry

    path = Path(request["path"])
    payload = exact_bytes(path, request["sha256"])
    document = open_document(path, include_brep=False, include_tessellation=False)
    sketch, = document.sketches
    circle, = (entity for entity in sketch.entities if type(entity.geometry) is CircleGeometry)
    point, = (entity for entity in sketch.entities if type(entity.geometry) is PointGeometry)
    sketch_id = sketch.attributes["native_object_id"]
    archive = SldprtArchive.from_bytes(payload)
    link = ReadNativeLink(archive, 0)
    roots = link.ResolvedValue.RootsValue
    profile, = (node for node in roots if node.ClassValue.NameValue == "moProfileFeature_c" and
                node.FieldsValue.get("f08") == sketch_id and ReadNativeName(node) == request["sketch"])
    boss, = (node for node in roots if node.ClassValue.NameValue == "moExtrusion_c" and ReadNativeName(node) == request["feature"])
    support, = boss.FieldsValue["f60"]["list"]["items"]
    require(support["o"] is profile, "the actual boss does not own the public profile")
    native_sketch = RequireNative(profile.FieldsValue["pd_f80"], "sgSketch")
    shape, centre_index = ReadCircleShape(native_sketch)
    fields = native_sketch.FieldsValue
    center = NativeRecord(fields["points"][centre_index]["point"])
    seam = NativeRecord(fields["points"][1 - centre_index]["point"])
    require(type(center["f0c"]) is int and center["f0c"] > 0 and center["f0c"] != seam["f0c"],
            "the native centre lacks a distinct actual point identity")
    coord = NativeRecord(center["pos"])
    metres = (coord["x"], coord["y"])
    dims = NativeRecord(fields["dims"])
    logical, = dims["log_g1"]
    fixed = NativeRecord(logical["d"])
    handle = RequireNative(fixed["h1"], "sgPointHandle")
    require(fixed["f80"] == 17 and not (dims["log_g2"] or dims["log_g3"]) and handle.FieldsValue["idx"] == centre_index,
            "the fixed relation and actual circle do not share the same native point")
    radial, mode, dim = ReadRadialDrive(link, native_sketch)
    require(mode == request["mode"] and radial.name == "D1",
            "the real radial dimension is on a different shape or not driving")
    expected = tuple(value * 1000.0 for value in metres)
    require(bits(shape.coordinates[:2]) == bits(expected) == bits(pair(circle.geometry.center)),
            "the public circle does not expose the raw typed centre projection")
    marker = projected_point(point, circle, native_sketch, center, sketch_id, link.StreamName, archive.require(link.StreamName), metres)
    require(bits(marker["expected_mm"]) == bits(pair(point.geometry.point)),
            "the fixed point does not expose the exact projection of its shared native centre")
    require(digest(path.read_bytes()) == request["sha256"], "the immutable archive changed during proof")
    return {"passed": True, "original_exact_predicate": point.geometry.point == circle.geometry.center,
            "public_circle_mm": pair(circle.geometry.center), "public_fixed_point_mm": pair(point.geometry.point),
            "raw_shared_metres_hex": [value.hex() for value in metres], "point_projection": marker,
            "profile_native_id": sketch_id, "profile_map": profile.IndexValue, "sketch_map": native_sketch.IndexValue,
            "centre_index": centre_index, "centre_mark": center["f0c"], "fixed_handle_map": handle.IndexValue,
            "fixed_logical_type": fixed["f80"], "radial_dimension_map": dim.IndexValue,
            "radial_dimension_type": dim.FieldsValue["f80"], "radial_arc_index": dim.FieldsValue["h1"].FieldsValue["idx"],
            "radial_display_handle_map": radial.TypedOwner["handle_index"]}


def frozen_worker(sdk, request, proof):
    path = sdk / WORKER_FILE
    exact_bytes(path, WORKER_SHA)
    spec = spec_from_file_location("frozen_circle_reader", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    centre_calls = 0

    def check(predicate, detail):
        nonlocal centre_calls
        if detail != OLD_CENTRE_CHECK:
            return module.require(predicate, detail)
        centre_calls += 1
        require(centre_calls == 1 and predicate is proof["original_exact_predicate"],
                "the frozen comparison no longer matches the independent observation")
        return module.require(proof["passed"], "shared centre identity and exact public projections differ")

    replay = FunctionType(module.worker.__code__, {**module.__dict__, "require": check})
    previous_input = sys.stdin
    try:
        sys.stdin = StringIO(dumps(request, allow_nan=False))
        report = replay(sdk)
    finally:
        sys.stdin = previous_input
    require(centre_calls == 1 and report["passed"] and report["typed_streams_exact"] == 2,
            "the frozen reader did not execute its entire prior check sequence")
    return {**report, "centre_proof": proof}


def worker():
    data = load(sys.stdin)
    sdk = Path(data["sdk"])
    require(digest(Path(__file__).read_bytes()) == data["tool_sha256"], "the supplemental source changed")
    sys.path[:0] = [str(sdk / "src"), str(sdk)]

    def deny_process(event, _args):
        if event in ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.fork", "os.forkpty"):
            raise PermissionError("the supplemental reader cannot start another tool")

    sys.addaudithook(deny_process)
    proof = prove_shared_centre(data["request"])
    return frozen_worker(sdk, data["request"], proof)


def main():
    parser = ArgumentParser(description="Repeat the locked H03/H04 readback with shared-centre ownership proof")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    workspace = args.workspace.resolve(strict=True)
    source = Path(__file__).resolve()
    output = args.output.resolve()
    require(not output.exists() and not output.is_relative_to(workspace) and not output.is_relative_to(source.parents[3]),
            "choose unused supplemental output outside the immutable packet and checkout")
    sdk, packet, native, prior, frozen_source = verified_workspace(workspace)
    tool_sha = digest(source.read_bytes())
    output.mkdir(parents=True)
    method_sha = save(output / "Method.json", {
        "schema": "kit.sw2026.end-condition-centre-supplement-method.v1",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(), "tool_sha256": tool_sha,
        "sdk_source_sha256": SOURCE_SHA, "sdk_source_revision": frozen_source["base"], "kit_worker_sha256": WORKER_SHA,
        "native_sha256": NATIVE_SHA, "packet_sha256": PACKET_SHA, "prior_readback_sha256": PRIOR_SHA,
        "criteria": "shared native centre index and marker owner, bit-equal raw metres, separate exact projections",
    })
    previous = {(row["case"], row["phase"]): row for row in prior["readbacks"]}
    rows = []
    for request in measured_inputs(workspace, packet, native):
        process = run((sys.executable, "-I", "-B", str(source), "worker"),
                      input=dumps({"sdk": str(sdk), "request": request, "tool_sha256": tool_sha}, allow_nan=False).encode(),
                      capture_output=True, check=False, timeout=120)
        require(process.returncode == 0, f"{request['case']} {request['phase']}: " + process.stderr.decode(errors="replace"))
        row = loads(process.stdout)
        key = (row["case"], row["phase"])
        require(key == (request["case"], request["phase"]) and row["file_sha256"] == request["sha256"],
                "the reader response does not match its request")
        if key in previous:
            require(all(row[name] == value for name, value in previous[key].items() if name != "pid"),
                    "one of the ten previously accepted states changed")
        rows.append(row)
    require(len(rows) == len({row["pid"] for row in rows}) == 12 and all(row["passed"] for row in rows) and
            sum(not row["centre_proof"]["original_exact_predicate"] for row in rows) == 2 and
            all((row["case"], row["phase"]) in previous or not row["centre_proof"]["original_exact_predicate"] for row in rows) and
            digest(source.read_bytes()) == tool_sha, "the supplemental worker inventory differs")
    verified_workspace(workspace)
    result = {"schema": "kit.sw2026.end-condition-centre-supplement.v1", "passed": True, "method_sha256": method_sha,
              "tool_sha256": tool_sha, "sdk_source_sha256": SOURCE_SHA, "sdk_source_files": frozen_source["file_count"],
              "packet_sha256": PACKET_SHA, "native_sha256": NATIVE_SHA, "prior_readback_sha256": PRIOR_SHA,
              "prior_passed": False, "prior_successful_reads": 10, "prior_exact_streams": 20,
              "fresh_sdk_processes": len(rows), "exact_streams": sum(row["typed_streams_exact"] for row in rows),
              "existing_successful_states_reproduced": len(previous), "readbacks": rows, "unverified": UNVERIFIED,
              "public_writer_qualified": False}
    result_sha = save(output / "Readback.json", result)
    print(dumps({"passed": True, "readback_sha256": result_sha, "method_sha256": method_sha,
                 "fresh_sdk_processes": len(rows), "exact_streams": result["exact_streams"]}, sort_keys=True))


if __name__ == "__main__":
    if sys.argv[1:] == ["worker"]:
        print(dumps(worker(), sort_keys=True, allow_nan=False))
    else:
        main()
