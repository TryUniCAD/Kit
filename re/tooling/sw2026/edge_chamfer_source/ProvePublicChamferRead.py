from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from math import dist, fsum, hypot
from pathlib import Path
import json
import subprocess
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent), str(HERE.parents[1] / "edge_fillet_source")]
from ChamferModel import compare_six, predict, values_si
from FilletModel import AXES, edge_role, stock
from convert import open_document
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfOwn import ReadChmfOwn
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureKinds import ChamferFeature, NativeFeature
from interchange.geometry.Models.Selection import SelectPathElem
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

TRIAL_SHA = "8db08a479cd2b3e29dd4d5ad38eec3e96631e0aec15f71868a37aea51d423f49"
SOURCE_LOCK_SHA = "2bce5961120ea7d8ea95ceaa5c10f7cbdbe6338152833357304647f432b86ff8"
FORMAT = "solidworks.sldprt"


def digest(data):
    return sha256(data).hexdigest()


def demand(condition, message):
    if not condition:
        raise ValueError(message)


def xyz(point):
    return point.x, point.y, point.z


def near(a, b):
    return dist(a, b) < 1e-11


def selected_witnesses(case, branch):
    _, bounds = stock(case)
    _, along, across, _, _ = edge_role(case)
    principal = across[branch[0]]
    bits = {index: int(case["corner"][AXES[index]] == "max") for index in across}
    edge = [sum(pair) / 2 if index == along else pair[bits[index]] for index, pair in enumerate(bounds)]
    face = [pair[bits[index]] if index == principal else sum(pair) / 2 for index, pair in enumerate(bounds)]
    return tuple(value * 1000.0 for value in edge), tuple(value * 1000.0 for value in face)


def semantic(doc, case, branch, owners):
    feature, = (step for step in doc.feature_timeline if step.kind is FeatureKind.KChamfer)
    steps = {step.id: step for step in doc.feature_timeline}
    prior, = feature.input_feature_ids
    boss = steps[prior]
    body, = doc.bodies
    demand(boss.order < feature.order and boss.name == body.name == "ChamferStockBoss"
           and boss.id == f"sldprt:feature:{owners.StockValue.FieldsValue['f08']}"
           and feature.id == f"sldprt:feature:{owners.FeatureValue.FieldsValue['f08']}"
           and body.final_feature_id == feature.id and feature.name == "DistanceAngleEdgeChamfer"
           and type(feature.definition) is ChamferFeature and feature.definition.mode == "distance_angle"
           and feature.definition.second_distance is None
           and tuple(item.name for item in doc.configurations) == ("Default",)
           and len(doc.feature_timeline) == 20, "public chamfer lost its typed native predecessor or ordered root inventory")
    sketch, = doc.sketches
    demand(sketch.id == boss.sketch_id and len(sketch.entities) == 4
           and len(sketch.closed_profile_entity_ids) == 1 and not sketch.constraints
           and next(plane.name for plane in doc.support_planes if plane.id == sketch.support_plane_id) == "Front Plane",
           "typed free stock loop or actual datum is missing")
    params = {value.id: value for value in doc.parameters}
    d1, d2 = (params[key] for key in feature.parameter_ids)
    values = values_si(case, False)
    demand(tuple((value.name, value.owner_id, value.role, value.value.kind, value.value.unit)
                 for value in (d1, d2)) == (("D1", feature.id, ParameterRole.KDriving, ValueKind.KLength, "mm"),
                                           ("D2", feature.id, ParameterRole.KDriving, ValueKind.KAngle, "rad"))
           and feature.definition.distance == d1.value and feature.definition.angle == d2.value
           and abs(d1.value.value - values[0] * 1000) < 1e-12 and d2.value.value == values[1]
           and not d1.expression and not d2.expression
           and (d1.attributes["persistent_dimension_id"], d2.attributes["persistent_dimension_id"])
           == (owners.Distance.DimensionNode.FieldsValue["f50"], owners.AngleValue.DimensionNode.FieldsValue["f50"])
           and d1.provenance.confidence == d2.provenance.confidence == 1.0
           and d1.provenance.spans != d2.provenance.spans, "live independent D1/D2 identities do not survive public read")
    selections = {value.id: value for value in doc.selections}
    selected = tuple(selections[key] for key in feature.selection_ids)
    demand(tuple(value.path for value in selected)
           == ((SelectPathElem("feature", prior, "edge"),), (SelectPathElem("feature", prior, "distance face"),))
           and all(value.point is not None and value.provenance.confidence == 1.0 for value in selected)
           and all(near(xyz(value.point), point) for value, point in zip(selected, selected_witnesses(case, branch), strict=True))
           and selected[0].provenance.spans != selected[1].provenance.spans,
           "ordered public edge and incident face picks differ from independent signed witnesses")
    return feature, d1, d2, selected


def face_vertices(model, face):
    loops = {loop.id: loop.coedge_ids for loop in model.loops}
    fins = {fin.id: fin for fin in model.coedges}
    edges = {edge.id: edge for edge in model.edges}
    vertices = {point.id: xyz(point.point) for point in model.vertices}
    ring, = face.loop_ids
    return tuple(vertices[edge.end_vertex_id if fin.reversed else edge.start_vertex_id]
                 for handle in loops[ring] for fin in (fins[handle],) for edge in (edges[fin.edge_id],))


def face_area(ring):
    origin = ring[0]
    points = tuple(tuple(a - b for a, b in zip(point, origin, strict=True)) for point in ring)
    return fsum(hypot(a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]) / 2
                for a, b in zip(points[1:], points[2:]))


def mass_centroid(model, along, stock_bounds):
    axes = ((along + 1) % 3, (along + 2) % 3)
    planar = {surface.id: surface for surface in model.surfaces}
    cap, = (face for face in model.faces if xyz(planar[face.surface_id].normal)[along] == -1.0)
    ring = face_vertices(model, cap)
    local = tuple(tuple(point[axis] - ring[0][axis] for axis in axes) for point in ring)
    pairs = tuple(zip(local, local[1:] + local[:1], strict=True))
    cross = tuple(a[0] * b[1] - b[0] * a[1] for a, b in pairs)
    twice = fsum(cross)
    result = [0.0] * 3
    result[along] = sum(stock_bounds[along]) / 2.0
    for index, axis in enumerate(axes):
        center = fsum((a[index] + b[index]) * weight for (a, b), weight in zip(pairs, cross, strict=True)) / (3 * twice)
        result[axis] = (ring[0][axis] + center) / 1000.0
    return result


def physical(doc, case, branch):
    expected = predict(case, values_si(case, False), tuple(branch))
    body, = doc.bodies
    model = doc.brep
    topo = body.topology
    demand(model is not None and not doc.brep_payloads and not model.validate(frozenset((body.id,)))
           and (topo.solid_count, topo.shell_count, topo.face_count, topo.edge_count, topo.vertex_count) == (1, 1, 7, 15, 10)
           and model.bodies[0].design_body_id == body.id
           and sorted(tuple(round(value / 1000.0, 12) for value in xyz(point.point)) for point in model.vertices)
           == sorted(tuple(round(value, 12) for value in point) for point in expected["vertices"]),
           "strict public body is not the real reconstructed chamfer boundary")
    figures = [
        (topo.volume * 1e-9, expected["volume"], 1e-21),
        (topo.surface_area * 1e-6, expected["area"], 1e-16),
        *((a, b, 1e-12) for a, b in zip(mass_centroid(model, expected["edge_axis"], expected["stock_bounds"]), expected["com"], strict=True)),
        *((a, b, 1e-16) for a, b in zip(sorted(face_area(face_vertices(model, face)) * 1e-6 for face in model.faces),
                                      expected["face_areas"], strict=True)),
    ]
    demand(all(compare_six(*entry)[2] for entry in figures), "strict public chamfer dimensions or mass properties differ")
    return {"coordinates_match": True, "six_significant_figure_checks": len(figures),
            "solids": 1, "faces": 7, "edges": 15, "vertices": 10}


def forbid_shape(data):
    try:
        open_document(BytesIO(data), source_format=FORMAT, strict=True)
    except SldprtFormat as error:
        demand("no readable Parasolid payload" in str(error), "unsupported chamfer bypassed the existing strict geometry boundary")
    else:
        raise ValueError("unsupported chamfer received strict geometry")


def failure_variants(archive):
    for label in ("unsupported_mode", "crossed_order", "different_event", "changed_live_driver", "changed_label"):
        link = ReadNativeLink(archive, 0, ReadChamfers=True)
        owned = ReadChmfOwn(link, ColdValue=True)
        fields = owned.FeatureValue.FieldsValue
        if label == "unsupported_mode":
            fields["f8c0"] = 0x11
        elif label == "crossed_order":
            for edge in (owned.SelectedRef, owned.DetachedRef):
                rows = edge.FieldsValue["f10"]
                rows[0], rows[1] = rows[1], rows[0]
        elif label == "different_event":
            owner = owned.SelectedRef.FieldsValue["f10"][0]["f08"].FieldsValue["f10"]["f10"]
            owner.FieldsValue["f10"]["f08"] += 1
        elif label == "changed_live_driver":
            owned.Distance.ParameterNode.FieldsValue["f58"] *= 1.25
        else:
            owned.Distance.DisplayNode.FieldsValue["f8a8"] += 0.25
        history = link.ResolvedValue
        changed, _ = WriteResolMut(history.RootsValue, history.ExtraFields, 19000, link.ConfigValue.MapValue,
                                   history.ContextValue, WriteChamfers=True)
        streams = dict(archive.Streams)
        streams[link.StreamName] = changed
        data = BuildSldprt(streams, FormatVersion=4)
        thin = open_document(BytesIO(data), source_format=FORMAT, strict=True, include_brep=False)
        step, = (value for value in thin.feature_timeline if value.kind is FeatureKind.KChamfer)
        demand(isinstance(step.definition, NativeFeature) and not any("distance-face" in value.id for value in thin.selections),
               "unqualified document projected into the selected-edge policy")
        forbid_shape(data)
        yield label


def worker(request, raw, saved):
    audit = BuildAudit(HERE.parents[1] / "serial/defs")
    sys.addaudithook(audit.InspectEvent)
    for codec in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        lookup(codec)
    for module in ("interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo",
                   "interchange.document.Models.DocumentProvenance", "interchange.document.Validation.DocumentValidate",
                   "interchange.document.Validation.DocumentAssemblyValidate", "interchange.document.Validation.DocumentFeatureValidate",
                   "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    audit.BeginBuild()
    archive = SldprtArchive.FromBytes(raw)
    link = ReadNativeLink(archive, 0, ReadChamfers=True)
    owners = ReadChmfOwn(link, ColdValue=True)
    light = open_document(BytesIO(raw), source_format=FORMAT, include_brep=False, configuration="Default", strict=True)
    full = open_document(BytesIO(raw), source_format=FORMAT, configuration="Default", strict=True)
    demand(light.brep is None and not light.brep_payloads, "no-Brep read secretly publishes physical geometry")
    demand(semantic(light, request["case"], request["branch"], owners) == semantic(full, request["case"], request["branch"], owners),
           "requesting geometry changes the actual feature, parameter, or selection ownership")
    response = physical(full, request["case"], request["branch"])
    warm = ReadChmfOwn(ReadNativeLink(SldprtArchive.FromBytes(saved), 0, ReadChamfers=True))
    demand(len(warm.Controllers) == 3 and warm.SelectedRef.FieldsValue["f70"] > 0, "existing warm selected-edge path changed")
    refusals = list(failure_variants(archive))
    demand(not audit.DeniedReads and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules),
           "chamfer readback used external data or the native runtime")
    return response | {"archive_sha256": digest(raw), "typed_saved_control_sha256": digest(saved),
                       "public_source_modes": 2, "ordered_picks": 2, "independent_drivers": 2,
                       "body_name": full.bodies[0].name, "ordered_root_rows": 20,
                       "runtime_accesses": 0, "refusals": refusals}


def supervisor(trial, saved_folder, output):
    raw = trial.read_bytes()
    demand(digest(raw) == TRIAL_SHA, "disclosed model-only archive authority differs")
    frozen = json.loads(raw)
    source_raw = (saved_folder / "SourceLock.json").read_bytes()
    demand(digest(source_raw) == SOURCE_LOCK_SHA, "disclosed native saved control authority differs")
    source = json.loads(source_raw)
    results = []
    for index, (case, row) in enumerate(zip(frozen["spec"]["cases"], frozen["cases"], strict=True)):
        candidate = trial.parent / row["path"]
        saved = saved_folder / f"Slot{index+1:02d}" / (case["name"] + ".SLDPRT")
        digest_a, digest_b = digest(candidate.read_bytes()), digest(saved.read_bytes())
        demand(digest_a == row["archive_sha256"] and digest_b == source["sources"][index]["original_sha256"],
               "disclosed model-only or native saved archive changed")
        request = {"case": case, "branch": row["branch"], "candidate": str(candidate), "saved": str(saved)}
        child = subprocess.run([sys.executable, "-I", "-B", str(HERE), "--worker"],
                               input=json.dumps(request).encode(), capture_output=True, check=False)
        demand(child.returncode == 0 and not child.stderr, child.stderr.decode())
        results.append(json.loads(child.stdout) | {"case": case["name"]})
    root = ROOT / "src/convert/adapters/solidworks/Core"
    paths = {*((root / "TypedResolved/Chamfers").glob("*.py")), root / "Adapter.py",
             root / "TypedResolved/Geometry/Display/ReadGeomMessage.py"}
    report = {"trial_sha256": TRIAL_SHA, "saved_control_lock": SOURCE_LOCK_SHA, "method_sha256": digest(HERE.read_bytes()),
              "reader_paths": {path.relative_to(ROOT).as_posix(): digest(path.read_bytes()) for path in sorted(paths)},
              "fresh_guarded_processes": 2, "native_runs": 0, "heldout_credit": 0, "results": results}
    with output.open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"receipt_sha256": digest(output.read_bytes()), "cases": len(results)}))


if __name__ == "__main__":
    cli = ArgumentParser()
    cli.add_argument("--worker", action="store_true")
    cli.add_argument("--trial", type=Path)
    cli.add_argument("--saved", type=Path)
    cli.add_argument("--output", type=Path)
    args = cli.parse_args()
    if args.worker:
        request = json.load(sys.stdin)
        print(json.dumps(worker(request, Path(request["candidate"]).read_bytes(), Path(request["saved"]).read_bytes())))
    else:
        supervisor(args.trial, args.saved, args.output)
