from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from struct import pack
import sys
from xml.etree.ElementTree import fromstring


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent), str(HERE.parents[1]), str(HERE.parents[1] / "serial")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(audit.InspectEvent)

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHeader import ReadMgrHeader
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import WriteMgrHeader
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Dimensions.ReadModelLinear import ReadModelLinear
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.History.ReadHistMut import ReadHistMut
from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KResolvedFeaturesStream, KeywordsStream
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckCutWrapper import CheckCutWrapper
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockAtom import ReadStockAtom
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadCutAtomId import ReadCutAtomId
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadManagedCutAtoms import ReadCutAtoms
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import ReadSingleNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.MakePrismLines import MakePrismLines
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import ReadPrismFrame
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismLoop import ReadPrismLoop
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Patterns.CheckPatOrig import CheckPatOrig
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadPatDrivers import ReadPatDrivers
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import CheckTreeAlias
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents

from CheckPatternAngleOwners import check_angles, node_fields, point, require, selected_target
from EmitLocalPattern import emit_pattern
from MakeLocalPattern import LocalPatternIntent, direction_fields
from MakeLocalPatternDrivers import PatternDriverStyle, driver_views
from MakePatternAngularPlane import AngularPlaneIntent
from MakePatternSeed import FrontBlindIntent, RaisedSeedIntent
from PatternAngleGeometry import offsets
from PatternAngleWire import read_resolved, write_resolved
from PatternHingeGeometry import derive_hinge


VERSION = 19000


def read_record(data, model_type):
    require(type(data) is dict and set(data) == set(model_type.__dataclass_fields__),
            "unexpected or missing modeled " + model_type.__name__ + " input")
    return data


def read_request(request):
    require(type(request) is dict and set(request) == {"seed", "axis", "plane", "annotation", "pattern"},
            "expected only modeled raised seed, direction and pattern intent")
    seed = read_record(request["seed"], RaisedSeedIntent)
    owners = {key: FrontBlindIntent(**read_record(seed[key], FrontBlindIntent)) for key in ("plate", "seed")}
    plane = read_record(request["plane"], AngularPlaneIntent)
    pattern = read_record(request["pattern"], LocalPatternIntent)
    styles = tuple(PatternDriverStyle(**{**read_record(style, PatternDriverStyle), "label_m": tuple(style["label_m"])})
                   for style in pattern["styles"])
    annotations = request["annotation"]
    require(type(annotations) is dict and set(annotations) == {"views", "active", "shown"},
            "expected explicit ordered profile, plane and pattern presentation inputs")
    return (RaisedSeedIntent(**{**seed, **owners}), request["axis"],
            AngularPlaneIntent(**{**plane, "shifted_point_m": tuple(plane["shifted_point_m"])}),
            annotations, LocalPatternIntent(**{**pattern, "styles": styles}))


def linked(container, streams):
    archive = SldprtArchive.FromBytes(container)
    require(archive.format_version == 4 and all(archive.Require(name) == raw for name, raw in streams.items())
            and all("Partition" not in name and "LocalBodies" not in name for name in archive.Streams),
            "complete cold pattern container lost owned bytes or stored an unexpected body cache")
    headers = tuple(ReadHeaderGraph(streams[name], VERSION) for name in ("Contents/Config-0-ModelHeader", "Header2"))
    config = ReadConfigMut(streams["Contents/Config-0"], VERSION, headers[0])
    manager = ReadCmgrMut(streams["Contents/CMgr"], VERSION)
    manager_header = ReadMgrHeader(streams["Contents/CMgrHdr2"], VERSION)
    definition = ReadModelDef(streams["Contents/Definition"], VERSION)
    metadata_names = tuple(f"_MO_VERSION_19000/{name}" for name in ("Biography", "History"))
    context = MakeLinkContext(config, manager)
    raw = streams[KResolvedFeaturesStream]
    roots, tail, observed = read_resolved(raw, config.MapValue, context)
    replay, rebuilt = write_resolved(roots, tail, config.MapValue, context)
    require(tail is None and replay == raw and observed == rebuilt
            and WriteCmgrMut(manager.RootValue, VERSION) == streams["Contents/CMgr"]
            and WriteMgrHeader(manager_header.RootValue, VERSION)[0] == streams["Contents/CMgrHdr2"]
            and WriteModelDef(definition.GraphValue).OutputValue == streams["Contents/Definition"]
            and WriteConfigMut(config.RootValue, VERSION, headers[0])[0] == streams["Contents/Config-0"]
            and all(WriteHeadGraph(h, VERSION) == streams[name]
                    for h, name in zip(headers, ("Contents/Config-0-ModelHeader", "Header2"), strict=True))
            and all(WriteHistMut(ReadHistMut(streams[name], VERSION).RootValue, VERSION)[0] == streams[name]
                    for name in metadata_names), "fresh cold pattern did not exactly reproduce all nine typed streams")
    return NativeLink(config, ResolvedGraph(roots, tail, observed, config.MapValue.CounterValue, VERSION, context, {}),
                      "Config-0", "Config-0-ResolvedFeatures"), headers


def observe_stocks(link, intent):
    roots = link.ResolvedValue.RootsValue
    model = link.ConfigValue.RootValue
    features = {node.FieldsValue["f08"]: node for node in roots}
    plate_profile, plate, seed_profile, seed, _, _, pattern = roots[-7:]
    operations = tuple(ReadExtrude(link, node, features, NewSolid=index == 1) for index, node in enumerate((plate, seed)))
    drivers = []
    for extrude, profile, expected in zip(operations, (plate_profile, seed_profile), (intent.plate, intent.seed), strict=True):
        value = extrude.RequireDepth()
        require(extrude.EndValue.FieldsValue["f128"] == 1 and extrude.ParentsValue == (profile,)
                and ReadNodeName(profile) == expected.sketch and ReadNodeName(extrude.NodeValue) == expected.feature
                and value.DepthValue.name == "D1" and value.DepthValue.native_value == expected.bounds_m[1][2],
                "seed and plate lost their own Front profiles or explicit D1 drivers")
        frame = ReadPrismFrame(profile, model, features)
        lines = MakePrismLines(ReadPrismLoop(profile, link))
        require((frame.origin.x, frame.origin.y, frame.origin.z) == (0.0, 0.0, 0.0)
                and (frame.z_axis.x, frame.z_axis.y, frame.z_axis.z) == (0.0, 0.0, 1.0),
                "stock profile lost canonical signed Front support")
        real_points = {(line.start.x / 1000.0, line.start.y / 1000.0) for line in lines}
        require(len(real_points) == 4 and all(
            any(max(abs(x - first), abs(y - second)) < 1e-15 for first, second in real_points)
            for x in (expected.bounds_m[0][0], expected.bounds_m[1][0])
            for y in (expected.bounds_m[0][1], expected.bounds_m[1][1])
        ), "typed rectangle did not preserve the independent model profile")
        drivers.append(value)
    require(drivers[0].Dimension is not drivers[1].Dimension and drivers[0].Parameter is not drivers[1].Parameter,
            "seed and plate share an editable driver")
    plate_atom, seed_atom, result_atom = candidate_atoms = (ReadStockAtom(plate, False), ReadStockAtom(seed, True), ReadStockAtom(pattern, True))
    selected = ReadSingleNode(pattern.FieldsValue["f548"], "moCompSolidBody_c")
    fields = selected.FieldsValue
    components = fields["f58"], ReadSingleNode(seed.FieldsValue["f548"], "moCompSolidBody_c").FieldsValue["f58"]
    identities = tuple(ReadCutAtomId(atom, node) for atom, node in zip(candidate_atoms, (plate, seed, pattern), strict=True))
    require(ReadCutAtoms(link) == set(candidate_atoms) and len(set(identities)) == 3
            and ReadSingleNode(pattern.FieldsValue["f988"].FieldsValue, "moICE_c") is seed and not ReadParents(pattern)
            and ReadSingleNode(pattern.FieldsValue["f530"], "moAtom_c") is seed_atom
            and ReadSingleNode(seed.FieldsValue["f530"], "moAtom_c") is plate_atom
            and tuple(atom.FieldsValue["f144"] for atom in candidate_atoms) == (1, 1, 0)
            and all(atom.FieldsValue["f180"] == atom.FieldsValue["f188"] == atom.FieldsValue["f1b0"] == 0 for atom in candidate_atoms)
            and fields["f108"] == plate.FieldsValue["f08"] and fields["f18"] == fields["f1c"] == identities[1]
            and fields["n110"] == 2 and tuple(row["v"] for row in fields["f110"]) == (identities[1], identities[0])
            and pattern.FieldsValue["f544"] == 1 and pattern.FieldsValue["f9f0"] == 1
            and fields["ff0"] is None and fields["f100"] == fields["f104"] == 0
            and components[0] is not components[1] and all(node.FieldsValue["owner"] is model for node in components),
            "cold pattern must consume the sole current seed result and retain original producer lineage")
    CheckCutWrapper(model, plate, seed, identities[0], IsCold=True)
    CheckTreeAlias(link, (selected, *components, *candidate_atoms))
    return identities, tuple(driver.DepthValue.TypedOwner["dimension_id"] for driver in drivers)


def observe_pattern(link, headers, request):
    seed_intent, axis_name, plane_intent, _, intent = request
    roots = link.ResolvedValue.RootsValue
    model = link.ConfigValue.RootValue
    require(len(roots) == len({node.FieldsValue["f08"] for node in roots}) == 24,
            "complete cold pattern requires one ordered root inventory")
    axis, plane, pattern = roots[-3:]
    require(tuple(ReadNodeName(node) for node in (axis, plane, pattern)) == (axis_name, plane_intent.name, intent.name),
            "generated hinge, datum and pattern root names differ from inputs")
    hinge = derive_hinge(seed_intent.plate.bounds_m, seed_intent.seed.bounds_m)
    angle = check_angles(model, roots, headers, hinge["ordered_endpoints_m"], plane_intent.angle_rad)
    atom_ids, depth_ids = observe_stocks(link, seed_intent)
    fields = node_fields(pattern, "moLPattern_c")
    require((fields["f9e0"], fields["f9fc"], fields["f1050"], fields["f1054"]) == (1, 1, 1, 0)
            and fields["f1298"] == int(intent.reverse) and fields["f1290"] is None
            and fields["f820"] is None and all(fields[key] == 0 for key in ("f12a0", "f12a4", "fa04", "fa08", "nf30", "na10", "na30"))
            and all(fields[key] is None for key in ("f1278", "f1280", "f12e8", "f12f0", "f1300", "f1308"))
            and len({fields[key] for key in ("f988", "f9d8", "f8d8", "f990")}) == 4
            and all(node_fields(fields[key], "suObList")["n"] == 0 for key in ("f9d8", "f8d8", "f990")),
            "complete cold pattern contains alternate pattern modes, visual application or extra selection")
    for slot in ("fa50", "fcb8"):
        CheckPatOrig(fields[slot])
    line = node_fields(fields["f1288"], "moLineRef_w")
    target, component = selected_target(line, "moCompRefPlane_c", "moRefPlane_c", model, roots, headers)
    expected = direction_fields(plane)
    line_fields = {key: point(line[key]) if key in ("fc8", "fe0") else line[key] for key in expected}
    require(target is plane and line["f0c"] == 0 and line["ff8"] == 0 and line["f58"].FieldsValue["f100"] == 0
            and pack("<8dB", *line_fields["fc8"], *line_fields["fe0"], line_fields["fb0"], line_fields["fb8"], line_fields["f68"])
            == pack("<8dB", *expected["fc8"], *expected["fe0"], expected["fb0"], expected["fb8"], expected["f68"]),
            "pattern direction differs from the actual registered angled plane and its finite display rectangle")
    CheckTreeAlias(link, (pattern, fields["f1288"], line["f58"], component, plane))
    direction = tuple(-value if intent.reverse else value for value in expected["fe0"])
    drivers = ReadPatDrivers(link, pattern)
    count, pitch, *_ = drivers
    require((count.LiveValue, pitch.LiveValue) == (intent.count, intent.pitch_m),
            "pattern does not expose its own authored count and pitch")
    start = tuple(map(float, seed_intent.seed.bounds_m[0]))
    finish = offsets(start, direction, intent.pitch_m)
    dim = pitch.DimensionValue.FieldsValue
    identifiers = tuple(driver.DimensionValue.FieldsValue["f50"] for driver in drivers)
    require((point(dim["f80"]), point(dim["fa0"])) == (start, finish) and point(dim["fc0"]) == (0.0, 0.0, 0.0)
            and identifiers == tuple(range(identifiers[0], identifiers[0] + len(drivers)))
            and identifiers[0] == plane.FieldsValue["f08"] + 1 and pattern.FieldsValue["f08"] == identifiers[-1] + 1
            and all(DatumTime(header, pattern.FieldsValue["f08"]) == seed_intent.epoch
                    and header.FieldsValue["f08"] == pattern.FieldsValue["f08"] + 1 for header in headers),
            "pattern lost its actual D3 witnesses or independent registered driver order")
    linear = ReadModelLinear(model)
    require((pitch.DisplayValue.FieldsValue["f58"], count.DisplayValue.FieldsValue["f58"], model.FieldsValue["fd44"])
            == (model.FieldsValue["fd44"] - 2, model.FieldsValue["fd44"] - 1, model.FieldsValue["fd44"]),
            "pattern display allocation differs from the model counter")
    for driver, style in zip(drivers, intent.styles, strict=True):
        display = driver.DisplayValue.FieldsValue
        require(tuple(display["f2b0"]) == driver_views(model, style)
                and point(display["f6a0"]["f38"]) == style.label_m and bool(display["fb60"] & 0x100) == style.design_intent
                and display["ff80"] == style.selected_leader and driver.ParameterValue.FieldsValue["f08"] == -1,
                "pattern dimensions changed an actual label, annotation role or selected leader")
        if driver.DimensionValue.ClassValue.NameValue == "ParallelPlaneDistanceDim_c":
            require(all(display[key] == value for key, value in linear.ProjectionValue.items()),
                    "distance display lost its actual model document style")
    return {"root_count": len(roots), "parent_root_ids": [plane.FieldsValue["f08"], roots[-4].FieldsValue["f08"]],
            "axis_id": axis.FieldsValue["f08"], "plane_id": plane.FieldsValue["f08"], "pattern_id": pattern.FieldsValue["f08"],
            "atom_ids": atom_ids, "depth_driver_ids": depth_ids, "next_display_id": model.FieldsValue["fd44"],
            "driver_order": [driver.NativeName for driver in drivers], "driver_ids": identifiers,
            "driver_values": [driver.LiveValue for driver in drivers], "display_cache_values": [driver.CacheValue for driver in drivers],
            "pitch_witnesses_m": [start, finish], "selected_line": line_fields,
            "signed_direction": direction, "angle_owner": angle["feature"], "stored_face_cache": None}


def observations_with_refusals(link, headers, request):
    observed = observe_pattern(link, headers, request)
    pattern, seed = link.ResolvedValue.RootsValue[-1], link.ResolvedValue.RootsValue[-4]
    fields = pattern.FieldsValue
    line = fields["f1288"].FieldsValue
    body = ReadSingleNode(fields["f548"], "moCompSolidBody_c").FieldsValue
    pitch = ReadPatDrivers(link, pattern)[1]
    probes = (
        ("crossed_line_plane", line["f58"].FieldsValue, "ff0", {**line["f58"].FieldsValue["ff0"], "f00": 4}),
        ("flipped_stored_direction", line, "fe0", {key: -value for key, value in line["fe0"].items()}),
        ("wrong_previous_result", body, "f110", list(reversed(body["f110"]))),
        ("wrong_retired_result", fields, "f530", seed.FieldsValue["f530"]),
        ("alternate_owner_geometry", pitch.DimensionValue.FieldsValue, "f80", pitch.DimensionValue.FieldsValue["fa0"]),
        ("active_dormant_driver_alias", fields, "f1268", fields["f1258"]),
        ("dropped_count_annotation", fields["f1258"].FieldsValue, "f2b0", []),
        ("borrowed_warm_appearance_state", fields, "f1054", 1),
        ("cleared_single_stock_dependency_bit", fields, "f9f0", 0),
    )
    refusals = {}
    for name, owner, key, value in probes:
        old = owner[key]
        owner[key] = value
        try:
            observe_pattern(link, headers, request)
        except ValueError as error:
            refusals[name] = str(error)
        finally:
            owner[key] = old
    require(len(refusals) == len(probes), "cold typed readback admitted altered provenance, pattern or atom ownership")
    return observed, refusals


def verify_keywords(raw, request, observed):
    seed_intent, axis_name, plane_intent, _, pattern = request
    tree = fromstring(raw[1:])
    require(tree.tag == "Keywords" and tree.attrib == {"Name": seed_intent.name, "id": str(seed_intent.epoch)}
            and len(tree) == 25, "cold pattern keywords must retain the actual feature inventory and model identity")
    owners = {int(row.get("id")): row for row in tree if row.tag != "Configuration"}
    expected = ((observed["axis_id"], axis_name, "Axis"), (observed["plane_id"], plane_intent.name, "Plane"),
                (observed["pattern_id"], pattern.name, "LPattern"))
    require(all(owners[identity].get("Name") == name and owners[identity].get("Type") == kind for identity, name, kind in expected)
            and [(row.get("Name"), float(row.text)) for row in owners[observed["pattern_id"]]]
            == [("D1", pattern.count), ("D3", pattern.pitch_m / .001)],
            "keyword pattern inventory must address the actual three roots and both active driver names")


def malformed_requests(request):
    seed, axis, plane, annotation, intent = request
    choices = (
        ("boolean_count", replace(intent, count=True)),
        ("coincident_footprints", replace(intent, pitch_m=.00001)),
        ("features_leave_plate", replace(intent, pitch_m=1.0)),
        ("duplicate_feature_name", replace(intent, name=seed.seed.feature)),
        ("invalid_annotation_role", replace(intent, styles=(replace(intent.styles[0], annotation_view="*Front"), *intent.styles[1:]))),
    )
    refusals = {}
    for name, changed in choices:
        try:
            emit_pattern(seed, axis, plane, annotation, changed)
        except ValueError as error:
            refusals[name] = str(error)
    require(len(refusals) == len(choices), "infeasible pattern geometry or alternate authored role reached output")
    return refusals


def main():
    for encoding in ("utf-16-le", "utf-8", "latin-1", "us-ascii"):
        lookup(encoding)
    data = json.load(sys.stdin)
    audit.BeginBuild()
    request = read_request(data)
    graph, streams, container = emit_pattern(*request)
    link, headers = linked(container, streams)
    observed, refusals = observations_with_refusals(link, headers, request)
    verify_keywords(streams[KeywordsStream], request, observed)
    result = {"native_container": {"bytes": len(container), "sha256": sha256(container).hexdigest(), "version": 4},
              "streams": {name: {"bytes": len(raw), "sha256": sha256(raw).hexdigest()} for name, raw in streams.items()},
              "map_counters": [link.ConfigValue.MapValue.CounterValue, link.ResolvedValue.MapValue.CounterValue],
              "typed_replay_count": 9, "observed": observed, "analytic_geometry": graph.measure, "bad_readback": refusals,
              "bad_input": malformed_requests(request), "guarded_runtime_reads": len(audit.DeniedReads)}
    if sys.argv[1:] == ["--binary"]:
        sys.stdout.buffer.write(container)
    elif not sys.argv[1:]:
        print(json.dumps(result, allow_nan=False, sort_keys=True))
    else:
        raise ValueError("unknown local pattern process output")


if __name__ == "__main__":
    main()
