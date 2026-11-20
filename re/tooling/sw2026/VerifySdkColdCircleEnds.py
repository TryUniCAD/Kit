from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from importlib import import_module
from itertools import chain
import json
from math import hypot, isclose, pi
from pathlib import Path, PureWindowsPath
import subprocess
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
from VerifySdkCircleEndRegistration import (
    EVENT, FREEZE_SHA, NATIVE_SHA, flip_direction, frozen_cases,
    identity, locked, read_json, require, switch_driver,
)


FORMAT = "solidworks.sldprt"
PACKET_SHA = "8f38fd02f84cd554342005cd2dd0457de879cd443e96d2721af05d770cbb0bdd"
OLD_RECEIPT = "re/solidworks/measurements/2026/SdkColdCircleRead01.json"
OLD_SHA = "d547bdbe3179275e989c1deffa2c1b95eca6925fa8b009afd8f49bb296183bdf"
REFUSAL = "SLDPRT contains no readable Parasolid payload"
MODE_REFUSAL = "cache free circle is outside the qualified support driver and direction profiles"
PHASES = ("open-save", "fresh-reopen", "edited-fresh-reopen")
MODES = {"H03MidPlane": "mid_plane", "H04TwoDirections": "two_lengths"}
GUARD = "src/convert/adapters/solidworks/Core/TypedResolved/Geometry/Circles/CheckCircMode.py"
TOOLS = (HERE.name, "VerifySdkCircleEndRegistration.py", "ProbeColdCircleRead.py", "ProbeColdCircleLegacy.py")


def xyz(value):
    return (value.x, value.y, value.z)


def xy(value):
    return (value.x, value.y)


def read_owner(parameter, native, stream):
    span, = parameter.provenance.spans
    require((span.stream, span.offset, span.offset + span.length, span.record_kind) ==
            (stream, native.StartOffset, native.EndOffset, "typed-archive-object"),
            "public parameter provenance differs from its actual typed owner")
    require(parameter.role == "driving" and parameter.value.unit == "mm" and
            parameter.value.value == native.FieldsValue["f58"] * 1000.0,
            "public parameter does not retain its live scalar projection")
    return {"parameter_id": parameter.id, "offset": span.offset,
            "length": span.length, "object_index": native.IndexValue,
            "value_mm": parameter.value.value}


def check_centre(actual, profile, resolved):
    from convert.adapters.solidworks.Core.TypedResolved.CirclePointIndex import FindCirclePoint
    from interchange.geometry.Models.GeometryCurves import CircleGeometry, PointGeometry

    sketch, = actual.sketches
    circle, = (entity for entity in sketch.entities if type(entity.geometry) is CircleGeometry)
    point, = (entity for entity in sketch.entities if type(entity.geometry) is PointGeometry)
    fields = profile.FieldsValue["pd_f80"].FieldsValue
    arc = fields["arcs"][0]["arc"]
    index = FindCirclePoint(arc, "fdc")
    seam_index = FindCirclePoint(arc, "fc8")
    centre, seam = (fields["points"][row]["point"] for row in (index, seam_index))
    centre_mm = tuple(centre["pos"][key] * 1000.0 for key in "xy")
    radius_mm = 1000.0 * hypot(*(seam["pos"][key] - centre["pos"][key] for key in "xy"))
    fixed, = fields["dims"]["log_g1"]
    fixed = fixed["d"]
    require(fixed["f80"] == 17 and fixed["h1"].ClassValue.NameValue == "sgPointHandle" and
            fixed["h1"].FieldsValue["idx"] == index and point.attributes["native_permanent_mark"] == centre["f0c"] and
            xy(circle.geometry.center) == xy(point.geometry.point) == centre_mm and circle.geometry.radius == radius_mm,
            "public circle and fixation differ from the exact typed arc projection")
    fixed_public, = (row for row in sketch.constraints if row.kind == "fixed")
    radial, = (row for row in sketch.constraints if row.kind == "diameter")
    require(tuple(row.entity_id for row in fixed_public.references) == (point.id,) and
            tuple(row.entity_id for row in radial.references) == (circle.id,) and radial.driving,
            "public constraints do not identify the actual circle and fixed point")
    radial_row, = fields["dims"]["val_g1"]
    radial_param, = (row for row in actual.parameters if row.id == radial.parameter_id)
    require(radial_param.owner_id == f"sldprt:feature:{profile.FieldsValue['f08']}",
            "diameter parameter has the wrong feature owner")
    return centre_mm, radius_mm, read_owner(radial_param, radial_row["d"].FieldsValue["f28"], resolved)


def check_boss(actual, link, source):
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
    from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude

    features = IndexFeatures(link)
    boss_node, = (row for row in features.values() if row.ClassValue.NameValue == "moExtrusion_c")
    owner = ReadExtrude(link, boss_node, features)
    boss_id = f"sldprt:feature:{boss_node.FieldsValue['f08']}"
    boss, = (row for row in actual.feature_timeline if row.id == boss_id)
    source_boss, = source.feature_timeline
    definition = boss.definition
    source_end = source_boss.definition
    mode = MODES[source.metadata["name"]]
    require(boss.name == source_boss.name and boss.sketch_id == actual.sketches[0].id and
            owner.ParentsValue == (owner.ProfileValue,) and
            str(definition.end_condition) == str(source_end.end_condition) == mode and
            definition.reversed == source_end.reversed and definition.symmetric == source_end.symmetric and
            definition.length.value == source_end.length.value and
            (definition.second_end_condition, definition.second_length) ==
            (source_end.second_end_condition, source_end.second_length),
            "public boss lost its actual sketch, direction or finite end mode")
    end = boss_node.FieldsValue["f818"]
    depths = (("D1", "f18", owner.RequireDepth()),)
    if source_end.second_length is not None:
        require(owner.SecondValue is not None, "the second end lacks its actual typed owner")
        depths += (("D2", "f20", owner.SecondValue),)
    else:
        require(owner.SecondValue is None, "mid-plane exposed an independent second end")
    parts = {row.name: row for row in actual.parameters if row.owner_id == boss_id}
    require(tuple(parts) == tuple(name for name, _, _ in depths) and
            boss.parameter_ids == tuple(row.id for row in parts.values()),
            "public boss parameters do not equal the active end inventory")
    observed = {}
    for name, slot, depth in depths:
        display = end.FieldsValue[slot]
        handle, = display.FieldsValue["f850"]
        dim = handle["o"].FieldsValue["ff0"]
        param = dim.FieldsValue["f28"]
        require(display is depth.DisplayValue and dim is depth.Dimension and param is depth.Parameter and
                depth.DepthValue.name == name and depth.DepthValue.TypedOwner["slot"] == "f818." + slot,
                "the active dimension does not alias its declared native slot")
        observed[name] = {**read_owner(parts[name], param, link.StreamName),
                          "slot": "f818." + slot, "dimension_index": dim.IndexValue,
                          "dimension_id": dim.FieldsValue["f50"]}
    body, = actual.bodies
    require(body.final_feature_id == boss_id and body.name == boss.name and body.provenance == boss.provenance,
            "design body does not bind its actual producing boss")
    return owner.ProfileValue, observed, boss_id


def check_solid(actual, source, centre_mm, radius_mm, stations):
    from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface

    source_sketch, = source.sketches
    authored = source_sketch.entities[0].geometry
    source_plane, = source.support_planes
    actual_plane, = (row for row in actual.support_planes if row.id == actual.sketches[0].support_plane_id)
    frame = source_plane.transform
    require(actual_plane.name == source_plane.name and actual_plane.transform == frame and
            all(isclose(a, b, rel_tol=1e-12, abs_tol=1e-12) for a, b in
                zip((*centre_mm, radius_mm), (*xy(authored.center), authored.radius), strict=True)),
            "actual arc and support differ from the frozen neutral request")
    solid, = actual.brep.bodies
    body, = actual.bodies
    region, = actual.brep.regions
    shell_use, = actual.brep.shell_uses
    shell, = actual.brep.shells
    require(solid.design_body_id == body.id and solid.region_ids == (region.id,) and region.solid and
            region.shell_use_ids == (shell_use.id,) and shell_use.shell_id == shell.id and shell.closed and
            set(shell.face_use_ids) == {row.id for row in actual.brep.face_uses} and
            {row.face_id for row in actual.brep.face_uses} == {row.id for row in actual.brep.faces} and
            not actual.brep.validate(frozenset((body.id,))),
            "closed B-rep does not link all faces to its design body")
    cylinder, = (row for row in actual.brep.surfaces if type(row) is CylinderSurface)
    caps = tuple(row for row in actual.brep.surfaces if type(row) is PlaneSurface)
    normal = xyz(frame.z_axis)
    centre = tuple(origin + centre_mm[0] * u + centre_mm[1] * v for origin, u, v in
                   zip(xyz(frame.origin), xyz(frame.x_axis), xyz(frame.y_axis), strict=True))
    points = [tuple(value + station * n for value, n in zip(centre, normal, strict=True))
              for station in stations]
    expected_caps = {(points[0], tuple(-n for n in normal)), (points[1], normal)}
    require(cylinder.radius == radius_mm and xyz(cylinder.origin) == points[0] and xyz(cylinder.axis) == normal and
            {(xyz(row.origin), xyz(row.normal)) for row in caps} == expected_caps and
            len(caps) == 2 and sorted(row.surface_id for row in actual.brep.faces) ==
            sorted(row.id for row in (cylinder, *caps)),
            "analytic cap and cylinder faces differ from the independently computed stations")
    topology = body.topology
    width = stations[1] - stations[0]
    expected = (pi * authored.radius ** 2 * width, 2 * pi * authored.radius * (authored.radius + width))
    require(topology.valid and (topology.solid_count, topology.shell_count, topology.face_count,
                                topology.edge_count, topology.vertex_count) == (1, 1, 3, 2, 2) and
            isclose(topology.volume, expected[0], rel_tol=1e-12) and
            isclose(topology.surface_area, expected[1], rel_tol=1e-12),
            "default read differs from the independent analytic mass-property calculation")
    spans = tuple(radius_mm * hypot(u, v) for u, v in zip(xyz(frame.x_axis), xyz(frame.y_axis), strict=True))
    expected_bounds = (tuple(min(p, q) - s for p, q, s in zip(*points, spans, strict=True)),
                       tuple(max(p, q) + s for p, q, s in zip(*points, spans, strict=True)))
    bounds = (xyz(topology.bounding_box.minimum), xyz(topology.bounding_box.maximum))
    require(bounds == expected_bounds, "body bounds differ from the analytic cylinder extents")
    return {"body_id": body.id, "body_label": body.name, "radius_mm": radius_mm, "axis": normal,
            "axial_interval_mm": stations, "cap_origins_mm": points, "bounds_mm": bounds,
            "volume_mm3": topology.volume, "area_mm2": topology.surface_area,
            "solids": 1, "shells": 1, "faces": 3, "edges": 2, "vertices": 2}


def cold_result(actual, archive, document):
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    require(actual.brep is not None and not actual.brep_payloads and not actual.validate(),
            "strict cold read did not return a complete neutral B-rep")
    diagnostic, = (row.attributes for row in actual.diagnostics if row.code == "sldprt.brep_reconstructed")
    require(diagnostic["method"] == "typed_parametric_circular_boss" and diagnostic["native_kernel_identity"] is False,
            "read claimed a different geometry route or native kernel identity")
    link = ReadNativeLink(archive, 0)
    profile, depths, boss = check_boss(actual, link, document)
    centre, radius, radial = check_centre(actual, profile, link.StreamName)
    end = document.feature_timeline[0].definition
    primary = end.length.value
    stations = (-primary, end.second_length.value) if end.reversed else (-primary / 2, primary / 2)
    require(diagnostic["axial_interval_mm"] == stations and
            diagnostic["depth_owner"]["object_index"] == depths["D1"]["object_index"],
            "geometry provenance differs from the actual primary depth")
    return {**check_solid(actual, document, centre, radius, stations), "boss_id": boss,
            "depth_owners": depths, "diameter_owner": radial, "centre_mm": centre}


def mode_rejection(archive):
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Core.Adapter import NativePartModel
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.ReadCircleGeom import ReadCircleGeom
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    try:
        ReadCircleGeom(ReadNativeLink(archive, 0), ReadCmgrMut(archive.require("Contents/CMgr"), 19000),
                       NativePartModel(archive, None), "sldprt:body:1")
    except ValueError as error:
        return str(error)
    raise ValueError("the unsupported profile passed the typed circle route")


def authored_negative(request):
    from convert.adapters.solidworks.Archive.Construction.Part.MakeCirclePart import MakeCirclePart
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectCircle import ProjectCircle
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
    from interchange.serialization.Deserialize import FromData
    from tests.Convert.Solidworks.Research.AdapterBridge.Circles.MakeWriteCircle import MakeWriteCircle

    document = FromData(request["document"])
    mode = request["negative"]
    if mode == "direction":
        document = flip_direction(document)
    elif mode == "driver":
        document = switch_driver(document)
    else:
        require(mode == "support", "undeclared authored near miss")
        other, = MakeWriteCircle("ColdCircleControl", False).support_planes
        actual, = document.support_planes
        document = replace(document, support_planes=(replace(actual, name=other.name, transform=other.transform),))
    return MakeCirclePart(document, MakePartRecipe(ProjectCircle(document), EVENT)).BytesValue


def worker(data):
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
    from convert import open_document
    from convert.api.ApiContext import GetRegistry
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Container.Parasolid import HasPayload
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import IsCacheAbsent
    from interchange.serialization.Deserialize import FromData
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

    kind = data["kind"]
    payload = None if kind == "negative" else locked(Path(data["path"]), data["sha256"])
    GetRegistry()
    for codec in ("utf-16-le", "utf-8", "latin-1", "utf-16"):
        lookup(codec)
    for module in ("DocumentAssemblyValidate", "DocumentFeatureValidate", "DocumentReferenceValidate"):
        import_module("interchange.document.Validation." + module)
    for module in ("DocumentProvenance", "DocumentWalk"):
        import_module("interchange.document.Models." + module)
    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    sys.addaudithook(audit.InspectEvent)
    if kind == "negative":
        payload = authored_negative(data)
    archive = SldprtArchive.from_bytes(payload)
    cache_absent = IsCacheAbsent(archive)
    partitions = sorted(row.name for row in archive.records if HasPayload(row.data))
    try:
        actual = open_document(payload, source_format=FORMAT)
    except ValueError as error:
        if kind != "saved":
            require(kind == "negative" and cache_absent and str(error) == REFUSAL and
                    mode_rejection(archive) == MODE_REFUSAL, "unsupported profile did not fail at its expected owner")
        result = {"status": "strict_refusal", "error": str(error)}
    else:
        require(kind != "negative", "an unqualified cold profile was admitted")
        if kind == "cold":
            require(cache_absent and not partitions and len(payload) == data["bytes"], "cold input custody differs")
            result = {"status": "analytic_cylinder", **cold_result(actual, archive, FromData(data["document"]))}
        else:
            require(kind == "saved" and not cache_absent and partitions and
                    all(row.code != "sldprt.brep_reconstructed" for row in actual.diagnostics),
                    "saved geometry was incorrectly credited to the cold path")
            result = {"status": "strict_open", "has_brep": actual.brep is not None,
                      "brep_payloads": len(actual.brep_payloads), "design_bodies": len(actual.bodies)}
    require(not audit.DeniedReads, "default read used runtime data or executable inputs")
    return {**result, **identity(payload), "native_payload_streams": partitions, "cold_eligible": cache_absent,
            "runtime_data_file_reads": len(audit.DeniedReads), "source_module_reads": len(audit.ModuleReads)}


def call(tool, arguments, request=None, exit_code=0):
    process = subprocess.run([sys.executable, "-I", "-B", str(HERE.parent / tool), *map(str, arguments)],
                             input=None if request is None else json.dumps(request, allow_nan=False),
                             capture_output=True, text=True, timeout=90)
    require(process.returncode == exit_code and not process.stderr,
            f"{tool} {arguments} returned {process.returncode}: {process.stderr or process.stdout}")
    return json.loads(process.stdout)


def live_worker(data):
    return call(HERE.name, ("worker",), data)


def saved_inputs(workspace, name, native_row):
    lanes = ("generated", "reference")
    require(set(native_row["lanes"]) == set(lanes), "native comparison lane inventory differs")
    for lane in lanes:
        label = name + lane.capitalize()
        rows = native_row["lanes"][lane]
        require(tuple(row["phase"] for row in rows) == PHASES and
                all(row["passed"] and row["source_immutable"] for row in rows) and
                [row["source_sha256"] for row in rows[1:]] == [row["saved_sha256"] for row in rows[:-1]],
                "immutable native save chain differs")
        for row in rows:
            basename = PureWindowsPath(row["saved_path"]).name
            require(basename == label + "Saved.SLDPRT", "native save path is outside the expected role")
            path = workspace / "Packet/Inspection" / label / row["phase"] / basename
            yield {"kind": "saved", "path": str(path), "sha256": row["saved_sha256"],
                   "bytes": row["saved_bytes"], "lane": lane, "phase": row["phase"]}


def run_pairs(workspace):
    packet = read_json(workspace / "Packet/Packet.json", PACKET_SHA)
    native = read_json(workspace / "Packet/Inspection/Result.json", NATIVE_SHA)
    require(packet["generated_freeze_sha256"] == FREEZE_SHA and native["packet_sha256"] == PACKET_SHA and
            len(native["controls"]) == 2 and all(row["healthy"] for row in native["controls"]),
            "paired source locks or native controls differ")
    rows = {}
    for (request, freeze), native_row in zip(frozen_cases(workspace), native["cases"], strict=True):
        name = native_row["name"]
        path = workspace / "Packet" / name / "Generated" / (name + ".SLDPRT")
        cold = live_worker({"kind": "cold", "path": str(path), **freeze["artifact"], **request})
        saved = {}
        for entry in saved_inputs(workspace, name, native_row):
            result = live_worker(entry)
            require(result["sha256"] == entry["sha256"] and result["bytes"] == entry["bytes"] and
                    not result["cold_eligible"] and result["native_payload_streams"],
                    "saved derivative custody or cache class differs")
            saved[entry["lane"] + "/" + entry["phase"]] = result
        near_misses = {role: live_worker({"kind": "negative", "negative": role, **request})
                       for role in ("direction", "driver", "support")}
        rows[name] = {"request_sha256": freeze["request_sha256"], "cold": cold, "native_saves": saved,
                      "authored_near_misses": near_misses}
    return rows


def existing_routes():
    old = read_json(ROOT / OLD_RECEIPT, OLD_SHA)["results"]
    results = {}
    def observe(key, tool, data, exit_code=0, args=()):
        current = call(tool, (ROOT, "read", *args), data, exit_code)
        previous = old[key]["result"]
        require({k: v for k, v in current.items() if k != "source_module_reads"} ==
                {k: v for k, v in previous.items() if k != "source_module_reads"},
                key + " changed an existing process observation")
        results[key] = current
    circle = "ProbeColdCircleRead.py"
    for variant in ("front", "top"):
        control = call(circle, (ROOT, "input", "--variant", variant))
        edited = call(circle, (ROOT, "input", "--variant", variant, "--edited"))
        observe("After" + variant + "1", circle, control)
        observe("Edit" + variant, circle, edited)
        for mutation in ("draft", "inactive-length", "scope", "radius", "support", "extra-parent"):
            observe("Reject" + variant + mutation, circle, {**control, "mutation": mutation}, 3)
    legacy = "ProbeColdCircleLegacy.py"
    for kind in ("prism", "pocket", "revolve"):
        control = call(legacy, (ROOT, "input", "--kind", kind))
        observe("Compat" + kind + "candidate", legacy, control)
    return results


def source_identity():
    files = chain(sorted((ROOT / "src").rglob("*.py")), (HERE.parent / name for name in TOOLS))
    return identity(json.dumps({str(path.relative_to(ROOT)): identity(path.read_bytes())["sha256"]
                                for path in files}, sort_keys=True).encode())["sha256"]


def main():
    if sys.argv[1:] == ["worker"]:
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True, allow_nan=False))
        return
    parser = ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    before = source_identity()
    pairs = run_pairs(args.workspace.resolve(strict=True))
    preserved = existing_routes()
    require(before == source_identity(), "SDK or proof source changed during qualification")
    result = {"schema": "kit.sw2026.cold-circle-end-read.v1", "passed": True, "cases": pairs,
              "existing_routes": preserved, "source_manifest_sha256": before,
              "reader_guard_sha256": identity((ROOT / GUARD).read_bytes())["sha256"],
              "tools_sha256": {name: identity((HERE.parent / name).read_bytes())["sha256"] for name in TOOLS},
              "frozen_input_manifest_sha256": FREEZE_SHA, "paired_native_sha256": NATIVE_SHA,
              "paired_packet_sha256": PACKET_SHA, "existing_routes_sha256": OLD_SHA,
              "native_processes_started": 0, "runtime_data_file_reads": 0, "original_source_inputs_opened": 0,
              "strict_read_processes": 39}
    encoded = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with args.output.open("xb") as output:
        output.write(encoded)
    print(json.dumps({"passed": True, **identity(encoded)}, sort_keys=True))


if __name__ == "__main__":
    main()
