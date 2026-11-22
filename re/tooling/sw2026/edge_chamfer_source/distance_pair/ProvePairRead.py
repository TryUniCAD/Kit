from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from math import dist, hypot
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(item) for item in (ROOT, ROOT / "src", HERE.parent, HERE.parents[1],
                                     HERE.parents[2] / "edge_fillet_source", HERE.parents[2])]

from ChamferModel import compare_six, predict_legs
from ObservePairArchives import guard, require
from ProvePublicChamferRead import (TRIAL_SHA, SOURCE_LOCK_SHA, face_area, face_vertices,
                                   forbid_shape, mass_centroid, physical, semantic, xyz)
from ProvePublicChamferWrite import EPOCH, authored
from convert import open_document
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.Adapter import NativePartModel
from convert.adapters.solidworks.Core.Preparation.Chamfers.PrepChmfPart import PrepChmfPart
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfOwn import ReadChmfOwn
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.TryColdChmf import ReadColdChmf, TryColdChmf
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureKinds import ChamferFeature

FORMAT = "solidworks.sldprt"
BASE = "9e939d42ca5eaa9e71c1c253c255010c9ef9c99e"
GENERATED = "f8b77a00518ea5e8918fbb4dbebc466611c9c38f6e676f09da1f9f3b09a026fb"
PAIRS = (
    ("equal", "EqualDistanceEdge.SLDPRT", "3d550644a3c0730f3204794d923e7351a6d82c95782d4d6570ce55cf0d8ccded",
     "001a7a009a25202ee98120ab700cc9af6de597e085b19aab1638ad628efd77cd", 18),
    ("unequal", "UnequalDistanceEdge.SLDPRT", "e4fdfc9bf94e51fa2d6f0e2fd69e533539ce85f71f1a6283b119648fc7e696bb",
     "21f5f6cb71555b448b670e1e0f647bc5ea147d139d27c3550591c3bf76957b4c", 2),
)
SIGNED_DOCS = (
    ("cc5ce7ed9c4406af627a6f56ff9a67aa76f8c403f71c5a2fc18df61ab072d124",
     "1b79d94ae2a21eaa68dcbbf241b885035f334c8b61307b274a232f13472618f4"),
    ("a2e872a54261e848856ed4a180efd0bd7a8b9a996a564a816a9350aa18239cf3",
     "57d7b7a775de8a470e7f833db7778c36704e1c8391d6de8b171e72c3be798c44"),
)


def digest(raw):
    return sha256(raw).hexdigest()


def pinned(path, expected):
    raw = path.read_bytes()
    require(digest(raw) == expected, f"disclosed input changed: {path.name}")
    return raw


def reject(action, reason, errors=(ValueError,)):
    try:
        action()
    except errors as error:
        require(reason in str(error), f"wrong refusal for {reason!r}: {error}")
    else:
        raise ValueError(f"expected refusal: {reason}")


def read_doc(raw, full):
    return open_document(BytesIO(raw), source_format=FORMAT, strict=True,
                         include_brep=full, configuration="Default")


def prepare(document, locator, epoch, private):
    return PrepChmfPart(document, BytesIO(), epoch,
                        WriteOptions(values={"final_destination": locator}),
                        AllowDistancePair=private)


def expected_pair(document):
    stock, step = document.feature_timeline
    sketch, = document.sketches
    ends = [entity.geometry.start for entity in sketch.entities]
    bounds = [(min(getattr(point, axis) for point in ends),
               max(getattr(point, axis) for point in ends)) for axis in "xy"]
    bounds.append((0.0, stock.definition.length.value))
    midpoints = [sum(interval) / 2 for interval in bounds]
    picks = {item.id: item for item in document.selections}
    edge, face = (xyz(picks[key].point) for key in step.selection_ids)
    close = lambda a, b: abs(a - b) < 1e-10
    along, = (index for index in range(3) if close(edge[index], midpoints[index]))
    primary, = (index for index in range(3) if not close(face[index], midpoints[index]))
    axes = tuple(index for index in range(3) if index != along)
    require(primary in axes and all(any(close(edge[i], end) for end in bounds[i]) for i in axes),
            "authored winners lack an actual signed edge and incident face")
    corners = {"xyz"[i]: "min" if close(edge[i], bounds[i][0]) else "max" for i in axes}
    first = step.definition.distance.value
    second = step.definition.second_distance.value if step.definition.second_distance else first
    legs = [first / 1000, second / 1000]
    if primary != axes[0]:
        legs.reverse()
    case = {"size_mm": [b - a for a, b in bounds], "center_mm": midpoints[:2],
            "edge_axis": "xyz"[along], "corner": corners}
    return predict_legs(case, legs), edge, face, primary


def pair_semantics(document, authored_doc, part, witnesses):
    owners = part.OwnersValue
    wanted = authored_doc.feature_timeline[-1]
    feature, = (row for row in document.feature_timeline if row.kind == FeatureKind.KChamfer)
    stock, = (row for row in document.feature_timeline if row.id in feature.input_feature_ids)
    body, = document.bodies
    sketch, = document.sketches
    require(type(feature.definition) is ChamferFeature and feature.definition == wanted.definition
            and feature.name == wanted.name and feature.id == f"sldprt:feature:{NativeNodeId(owners.FeatureValue)}"
            and stock.id == f"sldprt:feature:{NativeNodeId(owners.StockValue)}"
            and stock.operation == BooleanOp.KCreate and not feature.suppressed
            and stock.name == body.name == authored_doc.bodies[0].name
            and stock.sketch_id == sketch.id and len(sketch.entities) == 4 and len(document.feature_timeline) == 20
            and body.final_feature_id == feature.id and feature.input_feature_ids == (stock.id,),
            "ordinary read did not preserve native feature and body ownership")
    source_params = {value.id: value for value in authored_doc.parameters}
    actual_params = {value.id: value for value in document.parameters}
    drives = []
    for actual_id, source_id, driver in zip(feature.parameter_ids, wanted.parameter_ids,
                                            owners.DriversValue, strict=True):
        actual, source = actual_params[actual_id], source_params[source_id]
        dim_id = driver.DimensionNode.FieldsValue["f50"]
        require(actual.name == source.name == driver.NameValue and actual.value == source.value
                and actual.value.kind == ValueKind.KLength and actual.value.unit == "mm"
                and actual.owner_id == feature.id and actual.role == ParameterRole.KDriving
                and actual.expression is None and actual.provenance.confidence == 1
                and actual.attributes["persistent_dimension_id"] == dim_id
                and actual.attributes["native_value"] == driver.ValueSi
                and actual.attributes["native_unit"] == "m"
                and actual.attributes["typed_display_owner"] == NativeNodeSpan(part.LinkValue, driver.DisplayNode)
                and actual.attributes["typed_dimension_owner"] == NativeNodeSpan(part.LinkValue, driver.DimensionNode),
                "live distance driver lost its ordered typed parameter metadata")
        drives.append([actual.name, actual.value.value, dim_id, actual.id])
    picks = {value.id: value for value in document.selections}
    for pick_id, role, expected in zip(feature.selection_ids, ("edge", "distance face"), witnesses, strict=True):
        pick = picks[pick_id]
        parent, = pick.path
        require((parent.entity_kind, parent.entity_id, parent.subelement) == ("feature", stock.id, role)
                and dist(xyz(pick.point), expected) < 1e-10 and pick.provenance.confidence == 1,
                "selected edge or first carrier changed from its authored signed witness")
    return drives, feature.id, stock.id


def pair_geometry(document, expected, primary):
    body, = document.bodies
    mesh = document.brep
    topo = body.topology
    counts = (topo.solid_count, topo.shell_count, topo.face_count, topo.edge_count, topo.vertex_count)
    require(mesh is not None and not mesh.validate(frozenset((body.id,))) and not document.brep_payloads
            and counts == (1, 1, 7, 15, 10) and mesh.bodies[0].design_body_id == body.id,
            "clipped stock is not an exact closed neutral chamfer solid")
    coordinates = lambda vector: tuple(round(v, 12) for v in vector)
    require(sorted(coordinates(value / 1000 for value in xyz(p.point)) for p in mesh.vertices)
            == sorted(coordinates(p) for p in expected["vertices"]),
            "chamfer tip vertices disagree with the independent signed setbacks")
    actual_com = mass_centroid(mesh, expected["edge_axis"], expected["stock_bounds"])
    areas = sorted(face_area(face_vertices(mesh, face)) * 1e-6 for face in mesh.faces)
    bevel_points = {coordinates(point) for point in expected["bevel_vertices"]}
    bevel, = (face for face in mesh.faces if
              {coordinates(v / 1000 for v in point) for point in face_vertices(mesh, face)} == bevel_points)
    surface, = (row for row in mesh.surfaces if row.id == bevel.surface_id)
    normal = xyz(surface.normal)
    along = expected["edge_axis"]
    axes = [index for index in range(3) if index != along]
    corner = expected["source_edge"][0]
    components = [0.0] * 3
    for axis, leg in zip(axes, expected["legs_m"], strict=True):
        components[axis] = (1 if corner[axis] == expected["stock_bounds"][axis][1] else -1) / leg
    length = hypot(*components)
    require(dist(normal, [value / length for value in components]) < 1e-12,
            "bevel normal does not follow its independently oriented setbacks")
    actual = [topo.volume * 1e-9, topo.surface_area * 1e-6, *actual_com, *areas]
    predicted = [expected["volume"], expected["area"], *expected["com"], *expected["face_areas"]]
    tolerances = [1e-21, 1e-16, *([1e-12] * 3), *([1e-16] * 7)]
    require(all(compare_six(a, b, t)[2] for a, b, t in zip(actual, predicted, tolerances, strict=True)),
            "independent chamfer geometry measurements differ")
    return {"topology": counts, "comparison_count": len(actual), "exact_vertex_count": len(mesh.vertices),
            "bevel_normal": normal, "volume_mm3": topo.volume, "area_mm2": topo.surface_area,
            "centroid_mm": [value * 1000 for value in actual_com], "distance_axis": primary}


def mutate(archive, name):
    link = ReadNativeLink(archive, 0, ReadChamfers=True)
    owners = ReadChmfOwn(link, ColdValue=True, AllowDistancePair=True)
    fields = owners.FeatureValue.FieldsValue
    config, resolved = link.ConfigValue, link.ResolvedValue
    second = owners.SecondValue
    if name == "mode_word":
        fields["f8c0"] = 0x22
    elif name == "alternate_flags":
        fields["f860"] = 1
    elif name == "inactive_angle":
        fields["f818"] = fields["f810"]
    elif name == "stock_atom":
        fields["f538"] = None
    elif name == "edge_order":
        rows = owners.SelectedRef.FieldsValue["f10"]
        rows[0], rows[1] = rows[1], rows[0]
    elif name == "secondary_name":
        second.ParameterNode.FieldsValue["f18"].FieldsValue["f08"] = "D2"
    elif name == "secondary_persistent_id":
        second.DimensionNode.FieldsValue["f50"] -= 5
    elif name == "secondary_alias":
        fields["f820"] = fields["f810"]
    elif name == "missing_secondary":
        fields["f820"] = None
    elif name == "secondary_signed_frame":
        second.DimensionNode.FieldsValue["fe0"] = owners.Distance.DimensionNode.FieldsValue["fe0"]
    elif name == "secondary_label_view":
        second.DisplayNode.FieldsValue["f2b0"] = owners.Distance.DisplayNode.FieldsValue["f2b0"]
    elif name == "secondary_catalog_frame":
        catalog = config.RootValue.FieldsValue["fa48"].FieldsValue["items"]
        catalog[1]["o"].FieldsValue["f368"] = catalog[0]["o"].FieldsValue["f368"]
    else:
        raise ValueError("unknown authored negative")
    config_wire, remapped = WriteConfigMut(config.RootValue, 19000, config.HeaderValue)
    wire, _ = WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000, remapped.MapValue,
                            resolved.ContextValue, WriteChamfers=True)
    streams = dict(archive.Streams)
    streams.update({link.ConfigName: config_wire, link.StreamName: wire})
    return BuildSldprt(streams, FormatVersion=4)


def negative_pairs(archive, mode):
    rows = {
        "mode_word": "unsupported ordinary SOLIDWORKS chamfer mode",
        "alternate_flags": "unsupported ordinary SOLIDWORKS chamfer mode",
        "inactive_angle": "unsupported ordinary SOLIDWORKS chamfer mode",
        "stock_atom": "ordinary chamfer lacks actual stock",
        "edge_order": "chamfer surface keeper",
    }
    if mode == 2:
        rows |= {
            "secondary_name": "ordinary chamfer driver has unqualified local ownership",
            "secondary_persistent_id": "chamfer has alternate persistent dimension order",
            "secondary_alias": "ordinary chamfer driver has unqualified local ownership",
            "missing_secondary": "unsupported ordinary SOLIDWORKS chamfer mode",
            "secondary_signed_frame": "chamfer length witnesses differ",
            "secondary_label_view": "unqualified dimension view membership",
            "secondary_catalog_frame": "chamfer has an alternate signed display placement",
        }
    for name, reason in rows.items():
        invalid = mutate(archive, name)
        changed = SldprtArchive.from_bytes(invalid)
        model = NativePartModel(changed, None)
        reject(lambda: ReadColdChmf(changed, model, AllowDistancePair=True), reason)
        require(TryColdChmf(changed, model, ReadOptions()) is None,
                f"unqualified ordinary projection for {name}")
        if name in ("inactive_angle", "secondary_catalog_frame"):
            forbid_shape(invalid)
    return list(rows)


def check_pair(raw, request, document, archive, model, part):
    mode = request["mode"]
    qualified = TryColdChmf(archive, model, ReadOptions())
    require(qualified is not None and qualified.OwnersValue.ModeWord == mode,
            "ordinary cold selector did not bind the actual distance mode")
    require(TryColdChmf(archive, model, ReadOptions(extract_raw_brep=True)) is None,
            "analytic projection impersonates raw Parasolid")
    reject(lambda: ReadChmfOwn(part.LinkValue, AllowDistancePair=True), "unsupported ordinary SOLIDWORKS chamfer mode")
    expected, edge, face, primary = expected_pair(document)
    light, full = read_doc(raw, False), read_doc(raw, True)
    sem = pair_semantics(light, document, part, (edge, face))
    require(light.brep is None and not light.brep_payloads
            and sem == pair_semantics(full, document, part, (edge, face)),
            "geometry request changed the portable history")
    return pair_geometry(full, expected, primary) | {
        "drivers": sem[0], "feature_id": sem[1], "stock_id": sem[2],
        "refusals": negative_pairs(archive, mode),
        "ordinary_strict_reads": 2,
    }


def worker(request):
    raw = pinned(Path(request["archive"]), request["archive_sha256"])
    private = request["mode"] != 1
    if private:
        source = json.loads(pinned(Path(request["neutral"]), request["neutral_sha256"]))
        require(source["locator"] == request["locator"] and source["epoch"] == request["epoch"],
                "neutral request locator or epoch differs")
        document = CadDocument.from_json(json.dumps(source["document"]))
    else:
        saved = pinned(Path(request["saved"]), request["saved_sha256"])
        document = authored(request["case"], request["branch"][0])
    for codec in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "cp1252"):
        lookup(codec)
    for module in ("interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo",
                   "interchange.document.Models.DocumentProvenance", "interchange.document.Validation.DocumentValidate",
                   "interchange.document.Validation.DocumentAssemblyValidate", "interchange.document.Validation.DocumentFeatureValidate",
                   "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    denied = guard()
    archive = SldprtArchive.from_bytes(raw)
    model = NativePartModel(archive, None)
    part = ReadColdChmf(archive, model, AllowDistancePair=private)
    require(part.OwnersValue.ModeWord == request["mode"], "coded mode does not follow the actual feature")
    compiled = prepare(document, request["locator"], request["epoch"], private)
    require(compiled.BytesValue == raw, "model-only constructor diverges from the exact archive")
    if private:
        evidence = check_pair(raw, request, document, archive, model, part)
    else:
        light, full = read_doc(raw, False), read_doc(raw, True)
        current = [digest(json.dumps(doc.to_dict(), sort_keys=True, separators=(",", ":")).encode())
                   for doc in (light, full)]
        require(current == request["baseline_docs"], "existing signed public readback changed")
        require(semantic(light, request["case"], request["branch"], part.OwnersValue)
                == semantic(full, request["case"], request["branch"], part.OwnersValue),
                "existing signed feature or driver changed")
        warm = ReadChmfOwn(ReadNativeLink(SldprtArchive.from_bytes(saved), 0, ReadChamfers=True))
        require(len(warm.Controllers) == 3, "existing signed saved owner changed")
        evidence = physical(full, request["case"], request["branch"]) | {
            "baseline_documents": current, "saved_signed_control": request["saved_sha256"]}
    require(not denied and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules),
            "reader or composer used runtime inputs or CAD")
    return evidence | {"archive_sha256": digest(raw), "mode_word": request["mode"],
                       "runtime_reads": len(denied), "exact_model_regeneration": True}


def supervise(args):
    manifest = json.loads(pinned(args.compiled / "Generated.json", GENERATED))
    require(len(manifest["candidates"]) == len(PAIRS), "compiled pair inventory differs")
    requests = []
    for (label, name, archive_pin, neutral_pin, mode), row in zip(PAIRS, manifest["candidates"], strict=True):
        require((name, archive_pin, neutral_pin, mode) ==
                (row["name"], row["archive_sha256"], row["neutral_sha256"], row["mode_word"]),
                "compiled pair provenance differs")
        requests.append({"mode": mode, "archive_sha256": archive_pin,
                         "archive": str(args.compiled / "Candidates" / name),
                         "neutral_sha256": neutral_pin, "neutral": str(args.compiled / (label + "Neutral.json")),
                         "locator": manifest["destination"] + "\\" + name, "epoch": manifest["written_at"]})
    trial = json.loads(pinned(args.signed_trial, TRIAL_SHA))
    lock = json.loads(pinned(args.signed_saved / "SourceLock.json", SOURCE_LOCK_SHA))
    for index, (case, row, original, docs) in enumerate(zip(
            trial["spec"]["cases"], trial["cases"], lock["sources"], SIGNED_DOCS, strict=True)):
        requests.append({"mode": 1, "archive_sha256": row["archive_sha256"],
                         "archive": str(args.signed_trial.parent / row["path"]),
                         "saved_sha256": original["original_sha256"],
                         "saved": str(args.signed_saved / f"Slot{index + 1:02d}" / (case["name"] + ".SLDPRT")),
                         "locator": row["locator"], "epoch": EPOCH + index * 61,
                         "case": case, "branch": row["branch"], "baseline_docs": docs})
    results = []
    for request in requests:
        proc = subprocess.run([sys.executable, "-I", "-B", str(HERE), "--worker"],
                              input=json.dumps(request), text=True, capture_output=True, check=False, timeout=90)
        require(proc.returncode == 0 and not proc.stderr, proc.stderr + proc.stdout)
        results.append(json.loads(proc.stdout) | ({"neutral_sha256": request["neutral_sha256"]}
                                                 if "neutral_sha256" in request else {}))
    reader = ROOT / "src/convert/adapters/solidworks/Core/TypedResolved/Chamfers"
    sources = {HERE, *reader.glob("*.py"), reader.parents[1] / "Adapter.py",
               HERE.parent / "ObservePairArchives.py",
               *(HERE.parents[1] / name for name in ("ChamferModel.py", "ProvePublicChamferRead.py",
                                                     "ProvePublicChamferWrite.py")),
               HERE.parents[2] / "edge_fillet_source/FilletModel.py"}
    report = {"schema": "kit.sw2026.cold-distance-chamfer-readback.v2", "reader_base": BASE,
              "compiled_manifest_sha256": GENERATED, "signed_trial_sha256": TRIAL_SHA,
              "source_sha256": {path.relative_to(ROOT).as_posix(): digest(path.read_bytes())
                                for path in sorted(sources)},
              "fresh_guarded_workers": len(results), "native_processes": 0, "heldout_credit": 0,
              "results": results}
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(digest(args.output.read_bytes()))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--compiled", type=Path)
    parser.add_argument("--signed-trial", type=Path)
    parser.add_argument("--signed-saved", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True))
    elif not all((args.compiled, args.signed_trial, args.signed_saved, args.output)):
        parser.error("provide compiled pair, signed trial, signed controls and a fresh output file")
    else:
        supervise(args)
