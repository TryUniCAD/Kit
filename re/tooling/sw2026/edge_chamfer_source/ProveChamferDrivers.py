from argparse import ArgumentParser
from codecs import lookup
from functools import partial
from hashlib import sha256
from math import cos, dist, hypot, isclose, sin
from pathlib import Path
from struct import unpack
from subprocess import run
from types import SimpleNamespace
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent)]
VERSION = 19000
BASE = "55aac7066a286482593ab34619fd8fc17a4fb867"

from BuildChamferBoundary import require


def canonical(value):
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False).encode() + b"\n"


def digest(data):
    return sha256(data).hexdigest()


def vector(fields):
    return tuple(fields[key] for key in "xyz")


def compact(display, dimension, parameter):
    fields = display.FieldsValue
    return {"driver_si": parameter.FieldsValue["f58"], "persistent_id": dimension.FieldsValue["f50"],
            "view_id": fields["f2b0"][0]["v"], "text_kind": fields["f6a0"]["f10"],
            "label_station": fields["f8a8"], "label_clearance_m": fields["f8b0"],
            "witness_separation_m": fields["fad0"], "witness_length_m": -fields["ffe8"]
            if display.ClassValue.NameValue == "moDisplayAngularDim_c" else None}


def check_model():
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    sys.addaudithook(audit.InspectEvent)

    from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
    from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
    from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
    from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
    from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeCommonView import MakeCommonView
    from convert.adapters.solidworks.Archive.Construction.Nodes.InitNodeMut import InitNodeMut
    from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
    from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
    from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import MakePartHeaders
    from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import AnnoViewInput
    from convert.adapters.solidworks.Archive.Construction.Views.Annotations.PutAnnoCatalog import PutAnnoCatalog
    from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
    from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
    from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
    from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
    from convert.adapters.solidworks.Archive.Resolved.MakeResolvedCtx import MakeResolvedCtx
    from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
    from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfDim import ReadChmfDim
    from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
    from MakeChamferDrivers import make_drivers_mut

    tuple(lookup(codec) for codec in ("ascii", "utf-8", "utf-16-le", "latin-1"))
    raw_request = sys.stdin.buffer.read()
    request = json.loads(raw_request)
    audit.BeginBuild()
    case, shape, presentation = (request[key] for key in ("case", "shape", "presentation"))
    labels = SimpleNamespace(NameValue=case, ConfigName="Default", PlaneName="Top Plane", AxisValue="+Z",
                             SketchName="Shape", FeatureName="Stock")
    plan = MakePartRecipe(labels, 1795471200)
    ids = PersistentIds(request["first_id"], tuple(request["reservations"]))
    system = MakePartBaseMut(plan, labels, ids)
    model = system.RootValue
    header = MakePartHeaders(system, plan, ids)[0]
    views = PutAnnoCatalog(model, VERSION, tuple(AnnoViewInput(row["name"], row["basis"]) for row in request["catalog"]),
                          None, (None,))
    config_bytes, built = WriteConfigMut(model, VERSION, header)
    saved = ReadConfigMut(config_bytes, VERSION, header)
    require(WriteConfigMut(saved.RootValue, VERSION, header)[0] == config_bytes,
            "generated annotation catalog and style did not independently replay")
    context = {"model_is_part": 1, "model_compressed_stream": 1,
               "cmgr_f658": system.ManagerValue.FieldsValue["f658"]}

    def fresh(owner=model, mode=10):
        node = ArchiveNode(RuntimeClass("Chamfer_c", 1), {})
        InitNodeMut(node, "Neutral Bevel")
        node.FieldsValue.update(owner=owner, f2b0=VERSION, f8a0=mode)
        return node

    def encode(roots, seed):
        maps = ArchiveMaps(seed.CounterValue, seed)
        writer = BodyWriter(maps, MakeResolvedCtx(VERSION, seed, context, None), WriteBodyMut)
        for root in roots:
            WriteNodeMut(writer, root)
        return bytes(writer.OutputValue), maps.Snapshot()

    feature = fresh()
    expected_first = ids.NextValue
    graphs = make_drivers_mut(model, feature, shape, presentation, ids)
    created_ids = tuple(ids.Allocations[(graph.DimensionValue, "f50")] for graph in graphs)
    feature_id = ids.AllocateMut(feature)
    roots = tuple(feature.FieldsValue[field] for field in ("f810", "f818"))
    require(roots == tuple(graph.DisplayValue for graph in graphs)
            and all(graph.DisplayValue.FieldsValue["f850"][0]["o"] is graph.HandleValue
                    and graph.HandleValue.FieldsValue["ff0"] is graph.DimensionValue
                    and graph.DimensionValue.FieldsValue["f28"] is graph.ParameterValue
                    and all(item.FieldsValue["owner"] is feature for item in (
                        graph.DisplayValue, graph.HandleValue, graph.DimensionValue, graph.ParameterValue))
                    for graph in graphs)
            and len({item for graph in graphs for item in (
                graph.DisplayValue, graph.HandleValue, graph.DimensionValue, graph.ParameterValue)}) == 8
            and expected_first == created_ids[0] < created_ids[1] < feature_id,
            "driver graph lost local vertices, original feature ownership or allocation order")
    seed = built.MapValue
    archive, written = encode(roots, seed)
    saved_seed = saved.MapValue
    maps = ArchiveMaps(saved_seed.CounterValue, saved_seed)
    cursor = BinaryReader(archive)
    body_context = MakeResolvedCtx(VERSION, saved_seed, context, None)
    reader = GraphReader(cursor, maps, partial(ReadBodyMut, body_context), RequireCanonicalTags=True)
    read_roots = tuple(ReadNodeMut(reader) for _ in roots)
    read_map = maps.Snapshot()
    link = NativeLink(saved, ResolvedGraph(read_roots, None, read_map, saved_seed.CounterValue,
                                          VERSION, context, {}), "", "")
    reemitted, replay = encode(read_roots, saved_seed)
    require(cursor.GetRemaining() == 0 and archive == reemitted and replay == read_map
            and written.CounterValue == read_map.CounterValue, "typed drivers lost exact archive framing")
    observed = tuple(ReadChmfDim(link, root, bool(index)) for index, root in enumerate(read_roots))
    joined_view = views[presentation["view"]].FieldsValue["f360"]
    summaries = [compact(row.DisplayNode, row.DimensionNode, row.ParameterNode) for row in observed]
    require(tuple(item.NameValue for item in observed) == ("D1", "D2")
            and tuple(item.ValueSi for item in observed) == (shape["distance_m"], shape["angle_rad"])
            and tuple(row["persistent_id"] for row in summaries) == created_ids
            and [row["text_kind"] for row in summaries] == [18, 13]
            and all(row["view_id"] == joined_view for row in summaries)
            and all(graph.DisplayValue.FieldsValue["ff80"] == row.DisplayNode.FieldsValue["ff80"]
                    for graph, row in zip(graphs, observed, strict=True)),
            "typed driver did not recover the original value, view, leader or exact identifier")
    distance_fields, angle_fields = (item.DisplayNode.FieldsValue for item in observed)
    linear, angular = (item.DimensionNode.FieldsValue for item in observed)
    length, angle = (item.ValueSi for item in observed)
    witness = presentation["witness_length_m"]
    center = vector(angular["fc0"])
    require(center == vector(linear["f80"]) and linear["ff0"] == angular["ff0"]
            and isclose(dist(center, vector(linear["fa0"])), length, abs_tol=1e-12)
            and all(isclose(dist(center, vector(angular[key])), witness, abs_tol=1e-12)
                    for key in ("f80", "fa0"))
            and isclose(dist(vector(angular["f80"]), vector(angular["fa0"])), angle_fields["fad0"], abs_tol=1e-12)
            and isclose(angle_fields["fad0"], 2 * witness * sin(angle / 2), abs_tol=1e-12)
            and distance_fields["f8b0"] == abs(presentation["distance_text"][1])
            and angle_fields["f8b0"] == hypot(*presentation["angle_text_xy_m"])
            and angle_fields["f8a8"] == -0.5, "decoded geometry lost the neutral witness or label intent")

    def refuse(name, trial_shape, trial_presentation, match, *, node=None, allocator=ids):
        node = node or fresh()
        before = node.FieldsValue.copy(), allocator.CounterValue, allocator.Allocations.copy()
        try:
            make_drivers_mut(model, node, trial_shape, trial_presentation, allocator)
        except ValueError as error:
            require(match in str(error), f"unexpected {name} refusal: {error}")
            require(before == (node.FieldsValue, allocator.CounterValue, allocator.Allocations),
                    name + " changed a partially constructed graph")
            return name
        raise ValueError(name + " passed outside the model boundary")

    first_out, second_out = presentation["angle_text_xy_m"]
    refused = [
        refuse("foreign-owner", shape, presentation, "fresh owned", node=fresh(owner=None)),
        refuse("alternate-mode", shape, presentation, "local D1 or D2", node=fresh(mode=8)),
        refuse("unregistered-view", shape, presentation | {"view": "Missing"}, "one actual authored"),
        refuse("wrong-signed-view", shape, presentation | {"view": "*Top"}, "signed annotation orientation"),
        refuse("linear-label-witness", shape, presentation | {"distance_text": [0.5, 0.003]}, "beyond the second"),
        refuse("unproved-angular-branch", shape, presentation | {"angle_text_xy_m": [-first_out, -second_out]},
               "exterior to the first"),
        refuse("bad-angle", shape | {"angle_rad": 2.0}, presentation, "positive acute bevel"),
        refuse("bad-leader", shape, presentation | {"selected_leaders": [0, True]}, "signed leader"),
        refuse("allocator-exhaustion", shape, presentation, "persistent id capacity",
               allocator=PersistentIds(0x7ffffffd)),
        refuse("duplicate-slots", shape, presentation, "fresh owned", node=feature),
    ]
    handle = graphs[0].HandleValue
    for name, field, value in (("crossed-driver", "ff0", graphs[1].DimensionValue),
                               ("external-driver", "f100", graphs[1].ParameterValue)):
        previous = handle.FieldsValue[field]
        handle.FieldsValue[field] = value
        try:
            MakeCommonView(handle, True, 0, 18)
        except ValueError as error:
            require("local D1 or D2" in str(error), name + " refused for another reason")
            refused.append(name)
        else:
            raise ValueError(name + " reached the shared display initializer")
        finally:
            handle.FieldsValue[field] = previous
    require(not audit.DeniedReads, "chamfer graph accessed an outside input")
    return {"case": case, "intent_sha256": digest(raw_request), "config_bytes": len(config_bytes),
            "config_sha256": digest(config_bytes), "driver_archive_sha256": digest(archive),
            "driver_archive_bytes": len(archive), "archive_slots": [saved_seed.CounterValue, read_map.CounterValue],
            "drivers": summaries, "feature_id": feature_id, "exact_read_and_reserialize": True,
            "guarded_runtime_reads": len(audit.DeniedReads), "refusals": refused}


def check_source(folder, name, phase):
    from AuditTypedChamfer import (
        ReadChmfOwn, ReadNativeLink, SldprtArchive, expected_inputs, guard_runtime, predict, values_si,
    )
    from convert.adapters.solidworks.Archive.Construction.Dimensions.ReadModelLinear import ReadModelLinear
    from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import ReadRigidXform

    edited = phase == "edited"
    raw, case, side, _ = expected_inputs(folder, name, edited)
    blocked = guard_runtime()
    link = ReadNativeLink(SldprtArchive.from_bytes(raw), 0, ReadChamfers=True)
    source = ReadChmfOwn(link)
    model = link.ConfigValue.RootValue
    distance, angle = values_si(case, edited)
    layout = predict(case, (distance, angle), side)
    start, end = layout["source_edge"]
    index = layout["edge_axis"]
    sides = [value for value in range(3) if value != index]
    main, other = sides[side[0]], sides[1 - side[0]]
    require(side[1] == "tan", "disclosed source uses a different incident-side rule")
    center = [a / 2 + b / 2 for a, b in zip(start, end, strict=True)]
    sign = tuple(1.0 if isclose(start[axis], layout["stock_bounds"][axis][1], abs_tol=1e-15) else -1.0
                 for axis in range(3))
    anchor = center.copy()
    anchor[main] -= sign[main] * distance
    catalog = {row["o"].FieldsValue["f360"]: row["o"].FieldsValue
               for row in model.FieldsValue["fa48"].FieldsValue["items"]}
    style = ReadModelLinear(model)
    drivers = []
    for driver, length, is_angle in ((source.Distance, distance, False), (source.AngleValue, angle, True)):
        fields, dim = driver.DisplayNode.FieldsValue, driver.DimensionNode.FieldsValue
        row = compact(driver.DisplayNode, driver.DimensionNode, driver.ParameterNode)
        view = catalog[row["view_id"]]
        transform, offsets = ReadRigidXform(dim["ff0"])
        basis, zero = ReadRigidXform(view["f368"])
        columns = tuple(transform[i::3] for i in range(3))
        projection = lambda values: tuple(sum(p * q for p, q in zip(values, axis, strict=True)) for axis in columns)
        require(transform == basis and zero == (0.0, 0.0, 0.0) and abs(columns[2][index]) == 1
                and dist(offsets, tuple(-value for value in projection(anchor))) < 1e-12
                and fields["n2b0"] == len(fields["f2b0"]) == 1 and fields["f58"] == 0
                and all(fields[key] == x for key, x in style.ProjectionValue.items())
                and unpack("<d", fields["f5b0"]["data"])[0] == length,
                "native named view, local frame, shared style or exact live cache differs")
        row.update(view_name=view["f358"], label_direction=vector(fields["f880"]),
                   style_flags=fields["f8a4"], dimension_center_m=anchor)
        if not is_angle:
            u = tuple(sign[main] if n == main else 0.0 for n in range(3))
            v = tuple(sign[other] if n == other else 0.0 for n in range(3))
            delta = projection(tuple(b - a for a, b in zip(anchor, center, strict=True)))
            require(dist(vector(dim["f80"]), anchor) < 1e-12 and dist(vector(dim["fa0"]), center) < 1e-12
                    and dist(vector(dim["fe0"]), u) < 1e-12 and dist(vector(dim["fe8"]), v) < 1e-12
                    and dim["has_fe0"] == 1 and dist(vector(fields["f988"]), delta) < 1e-12
                    and dist(vector(fields["f9a0"]), delta) < 1e-12
                    and abs(row["witness_separation_m"] - distance) < 1e-12,
                    "native distance references no longer join the edge center and actual side")
        else:
            first, second = [vector(dim[key]) for key in ("f80", "fa0")]
            radius = row["witness_length_m"]
            a, b = anchor.copy(), anchor.copy()
            a[main] -= sign[main] * radius * cos(angle)
            a[other] += sign[other] * radius * sin(angle)
            b[main] -= sign[main] * radius
            first_local = projection(tuple(p - q for p, q in zip(a, anchor, strict=True)))
            second_local = projection(tuple(p - q for p, q in zip(b, anchor, strict=True)))
            u, v = tuple(tuple(-c / radius for c in x) for x in (first_local, second_local))
            label = row["label_direction"]
            side_test = (u[0] * label[1] - u[1] * label[0]) * (u[0] * v[1] - u[1] * v[0])
            require(dim["has_fe0"] == 0 and dist(vector(dim["fc0"]), anchor) < 1e-12
                    and dist(first, a) < 1e-12 and dist(second, b) < 1e-12
                    and abs(radius - 0.01) < 1e-12
                    and dist(vector(fields["f958"]), first_local) < 1e-12
                    and dist(vector(fields["f988"]), second_local) < 1e-12
                    and dist(vector(fields["ffb8"]), u) < 1e-12 and dist(vector(fields["ffd0"]), v) < 1e-12
                    and abs(row["witness_separation_m"] - 2 * radius * sin(angle / 2)) < 1e-12
                    and all(abs(fields[key] - expected) < 1e-12 for key, expected in (
                        ("fff0", 0.0), ("fff8", -radius), ("f1000", 0.0), ("f1008", 1),
                        ("f100c", 0), ("f1010", 1), ("f1018", 24)))
                    and (row["label_station"] == -0.5) == (side_test < -1e-8),
                    "native angular references or first-exterior label branch differs")
            row["first_exterior_score"] = side_test
        drivers.append(row)
    feature_id = source.FeatureValue.FieldsValue["f08"]
    require(drivers[0]["persistent_id"] + 1 == drivers[1]["persistent_id"] == feature_id - 1
            and not blocked, "source driver audit lost consecutive ordered identity or read an outside file")
    return {"source_sha256": digest(raw), "case": name, "phase": phase, "feature_id": feature_id,
            "drivers": drivers, "guarded_runtime_reads": len(blocked)}


def run_process(*args, data=None):
    result = run((sys.executable, "-I", "-B", str(HERE), *args), input=data, capture_output=True,
                 check=False, timeout=45)
    require(result.returncode == 0 and not result.stderr, result.stderr.decode())
    return result.stdout


def model_requests():
    x, y, z = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
    nx, nz = (-1.0, 0.0, 0.0), (0.0, 0.0, -1.0)
    top = {"name": "*Top", "basis": (x, nz, y)}
    front = {"name": "*Front", "basis": (x, y, z)}
    first = {"case": "NeutralAxial", "first_id": 11, "reservations": [63],
             "catalog": [{"name": "*Back", "basis": (nx, y, nz)}, top],
             "shape": {"body_id": "BodyA", "stock_bounds_m": [[-.02, .036], [-.042, .049], [.005, .039]],
                       "edge_axis": 2, "corner": {"0": 1, "1": 0}, "distance_axis": 0,
                       "distance_m": .00475, "angle_rad": .71},
             "presentation": {"view": "*Back", "distance_text": [1.375, -.009],
                              "angle_text_xy_m": [0.0, .01225], "witness_length_m": .014,
                              "design_intent": False, "selected_leaders": [-2, 24]}}
    second = {"case": "NeutralCross", "first_id": 68, "reservations": [100],
              "catalog": [top, front, {"name": "*Left", "basis": (z, y, nx)}],
              "shape": {"body_id": "BodyB", "stock_bounds_m": [[-.025, .044], [-.035, .052], [.008, .033]],
                        "edge_axis": 0, "corner": {"1": 1, "2": 1}, "distance_axis": 2,
                        "distance_m": .00525, "angle_rad": .93},
              "presentation": {"view": "*Left", "distance_text": [1.625, .00625],
                               "angle_text_xy_m": [0.0, -.013], "witness_length_m": .016,
                               "design_intent": True, "selected_leaders": [71, -3]}}
    return first, second


def compare(folder, output):
    folder, output = folder.resolve(), output.resolve()
    require(not output.is_relative_to(folder), "proof output must preserve immutable source custody")
    models = []
    for model in model_requests():
        raw = canonical(model)
        first, second = (run_process("--model", data=raw) for _ in range(2))
        require(first == second, "isolated generation from the same neutral model is not deterministic")
        result = json.loads(first)
        require(result["intent_sha256"] == digest(raw) and result["guarded_runtime_reads"] == 0,
                "model result did not bind its exact independent intent")
        models.append(result)
    require(len({row["drivers"][0]["view_id"] for row in models}) == 2
            and len({row["driver_archive_sha256"] for row in models}) == 2
            and len({row["config_bytes"] for row in models}) == 2,
            "independent models failed to vary actual naming, body inputs or library extent")
    names = ("ChamferDistanceAxialA", "ChamferAngleTopB")
    native = [json.loads(run_process("--source", str(folder), name, phase))
              for name in names for phase in ("original", "edited")]
    initial, edited = native[:2]
    require(initial["drivers"][0]["driver_si"] != edited["drivers"][0]["driver_si"]
            and initial["drivers"][0]["label_clearance_m"] == edited["drivers"][0]["label_clearance_m"]
            and [row["drivers"][1]["label_station"] for row in native] == [1.5, 1.5, 1.5, -0.5],
            "source did not discriminate automatic text state from actual editable geometry")
    paths = (HERE, HERE.with_name("MakeChamferDrivers.py"),
             *(ROOT / "src/convert/adapters/solidworks/Archive/Construction/Dimensions" / f"{name}.py"
               for name in ("RequireDisplay", "RequireChmfView")))
    report = {"schema": "kit.sw2026.edge-chamfer-model-drivers.v1", "baseline_revision": BASE,
              "disclosed_source_lock_sha256": digest((folder / "DisclosedSourceLock.json").read_bytes()),
              "owner_code_sha256": {path.relative_to(ROOT).as_posix(): digest(path.read_bytes()) for path in paths},
              "neutral_writer_processes": 4, "guarded_disclosed_read_processes": 4, "model_cases": models,
              "disclosed_source_observations": native, "native_launches": 0, "native_outputs": 0,
              "heldout_reader_or_writer_credit": 0, "unsupported_angular_station": 1.5}
    with output.open("xb") as sink:
        sink.write(canonical(report))
    return {"receipt_sha256": digest(output.read_bytes()), "neutral_writer_processes": 4,
            "guarded_disclosed_read_processes": 4}


if __name__ == "__main__":
    parser = ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--model", action="store_true")
    modes.add_argument("--source", nargs=3)
    modes.add_argument("--compare", nargs=2, type=Path)
    args = parser.parse_args()
    if args.model:
        result = check_model()
    elif args.source:
        result = check_source(Path(args.source[0]), *args.source[1:])
    else:
        result = compare(*args.compare)
    sys.stdout.buffer.write(canonical(result))
