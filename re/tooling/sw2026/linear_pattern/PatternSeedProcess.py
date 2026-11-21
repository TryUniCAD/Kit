from codecs import lookup
from dataclasses import replace
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent)]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(audit.InspectEvent)

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import MakePartHeaders
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckCutWrapper import CheckCutWrapper
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockAtom import ReadStockAtom
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadCutAtomId import ReadCutAtomId
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadManagedCutAtoms import ReadCutAtoms
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import ReadSingleNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.MakePrismLines import MakePrismLines
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import ReadPrismFrame
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismLoop import ReadPrismLoop
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import CheckTreeAlias
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude

from CheckPatternAngleOwners import require
from MakePatternSeed import FrontBlindIntent, RaisedSeedIntent, make_raised_seed
from PatternHingeGeometry import box_points


def read_intent(data):
    require(type(data) is dict and set(data) == set(RaisedSeedIntent.__dataclass_fields__),
            "raised-seed request requires explicit neutral model identities only")
    blind = tuple(data[key] for key in ("plate", "seed"))
    require(all(type(row) is dict and set(row) == set(FrontBlindIntent.__dataclass_fields__) for row in blind),
            "expected two independent explicitly modeled rectangular prisms")
    return RaisedSeedIntent(**{**data, **{role: FrontBlindIntent(**row) for role, row in zip(("plate", "seed"), blind, strict=True)}})


def observe(link, intent, headers):
    roots = link.ResolvedValue.RootsValue
    model = link.ConfigValue.RootValue
    root_ids = [NativeNodeId(root) for root in roots]
    require(len(roots) == len(set(root_ids)) == 21, "raised seed graph has a duplicate or alternate feature root")
    features = dict(zip(root_ids, roots, strict=True))
    profiles = roots[-4], roots[-2]
    plate, seed = roots[-3], roots[-1]
    expectations = intent.plate, intent.seed
    operations = tuple(ReadExtrude(link, node, features, NewSolid=index == 1) for index, node in enumerate((plate, seed)))
    measures = []
    for position, (feature, profile, operation, expected) in enumerate(zip((plate, seed), profiles, operations, expectations, strict=True)):
        fields, end = feature.FieldsValue, operation.EndValue.FieldsValue
        require(operation.ParentsValue == (profile,) and ReadNodeName(profile) == expected.sketch and ReadNodeName(feature) == expected.feature
                and fields["f810"] == position - 1 and fields["f544"] == 1 and fields["f838"] == 0.0
                and all(end[key] == value for key, value in (("f08", 1), ("f0c", 0), ("f10", 0), ("f8c", 0), ("f128", 1),
                                                              ("f20", None), ("fc8", None), ("fd0", None))),
                "raised seed has an alternate feature or extrusion end")
        depth = operation.RequireDepth()
        expected_low, expected_high = box_points(expected.bounds_m)
        require(depth.DepthValue.name == "D1" and depth.DepthValue.native_value == expected_high[2],
                "raised rectangular extrusion lost its actual independent editable D1")
        frame = ReadPrismFrame(profile, model, features)
        lines = MakePrismLines(ReadPrismLoop(profile, link))
        require((frame.origin.x, frame.origin.y, frame.origin.z) == (0.0, 0.0, 0.0)
                and (frame.z_axis.x, frame.z_axis.y, frame.z_axis.z) == (0.0, 0.0, 1.0),
                "merged stock profile changed original Front support")
        xs, ys = tuple(line.start.x * .001 for line in lines), tuple(line.start.y * .001 for line in lines)
        bounds = ((min(xs), min(ys), 0.0), (max(xs), max(ys), depth.DepthValue.native_value))
        require(all(abs(a-b) < 1e-15 for p, q in zip(bounds, (expected_low, expected_high), strict=True)
                    for a, b in zip(p, q, strict=True)),
                "actual owned rectangular sketch bounds differ from authored stock")
        CheckTreeAlias(link, (depth.DisplayValue, depth.HandleValue, depth.Dimension, depth.Parameter))
        measures.append({"feature": NativeNodeId(feature), "profile": NativeNodeId(profile), "names": [expected.sketch, expected.feature],
                         "bounds_m": bounds, "depth_owner": depth.DepthValue.TypedOwner})
    depths = tuple(owner.RequireDepth() for owner in operations)
    require(len({member for depth in depths for member in (depth.DisplayValue, depth.HandleValue, depth.Dimension, depth.Parameter)}) == 8
            and len({depth.Dimension.FieldsValue["f50"] for depth in depths}) == 2
            and all(DatumTime(header, NativeNodeId(node)) == intent.epoch for header in headers for node in (plate, seed)),
            "raised seed shares an editable driver or has an unowned creation event")
    input_atom, output_atom = ReadStockAtom(plate, False), ReadStockAtom(seed, True)
    ids = ReadCutAtomId(input_atom, plate), ReadCutAtomId(output_atom, seed)
    manager = model.FieldsValue["fd88"]
    require(ReadCutAtoms(link) == {input_atom, output_atom} and ids[0] < ids[1] == manager["f260"]
            and tuple(row["o"] for row in manager["atoms"]) == (input_atom, output_atom)
            and tuple(atom.FieldsValue["f144"] for atom in (input_atom, output_atom)) == (1, 0)
            and all(atom.FieldsValue["f180"] == atom.FieldsValue["f188"] == atom.FieldsValue["f1b0"] == 0
                    for atom in (input_atom, output_atom))
            and plate.FieldsValue["has_f548"] == 0 and seed.FieldsValue["has_f548"] == 1
            and ReadSingleNode(seed.FieldsValue["f530"], "moAtom_c") is input_atom,
            "consumed and output atoms do not retain single live stock history")
    CheckCutWrapper(model, plate, seed, ids[0], IsCold=True)
    wrapper = ReadSingleNode(seed.FieldsValue["f548"], "moCompSolidBody_c")
    CheckTreeAlias(link, (wrapper, wrapper.FieldsValue["f58"]))
    return {"roots": len(roots), "operations": measures, "actual_atoms": ids, "manager_counts": [manager["n6c"], manager["f260"]],
            "atom_map_indices": [node.IndexValue for node in (input_atom, output_atom)], "consumed": [1, 0],
            "base_and_immediate": [wrapper.FieldsValue["f108"], wrapper.FieldsValue["f18"]], "wrapper_face": None}


def altered_owner_refusals(link, intent, headers):
    plate, seed = link.ResolvedValue.RootsValue[-3], link.ResolvedValue.RootsValue[-1]
    consumed = ReadSingleNode(seed.FieldsValue["f530"], "moAtom_c")
    result = ReadSingleNode(seed.FieldsValue["f528"], "moAtom_c")
    wrapper = ReadSingleNode(seed.FieldsValue["f548"], "moCompSolidBody_c").FieldsValue
    probes = (
        ("wrong_base_producer", wrapper, "f108", NativeNodeId(seed)),
        ("wrong_selected_result", wrapper, "f18", result.FieldsValue["f140"]),
        ("self_consumption", seed.FieldsValue, "f530", {"n": 1, "items": [{"o": result}]}),
        ("prior_atom_still_live", consumed.FieldsValue, "f144", 0),
        ("foreign_profile", seed.FieldsValue, "f60", plate.FieldsValue["f60"]),
        ("shared_depth_handle", seed.FieldsValue["f818"].FieldsValue, "f18", plate.FieldsValue["f818"].FieldsValue["f18"]),
    )
    refusals = {}
    for role, owner, slot, changed in probes:
        prior = owner[slot]
        owner[slot] = changed
        try:
            observe(link, intent, headers)
        except ValueError as error:
            refusals[role] = str(error)
        finally:
            owner[slot] = prior
    require(len(refusals) == len(probes), "malformed selected body or sketch ownership reached accepted readback")
    return refusals


def invalid_geometries(intent):
    seed_lo, seed_hi = box_points(intent.seed.bounds_m)
    _, plate_hi = box_points(intent.plate.bounds_m)
    replacements = {
        "disjoint_footprint": ((plate_hi[0] + seed_lo[0], *seed_lo[1:]), (plate_hi[0] + seed_hi[0], *seed_hi[1:])),
        "below_plate": (seed_lo, (*seed_hi[:2], plate_hi[2] / 2.0)),
        "offset_start": ((*seed_lo[:2], seed_hi[2] / 10.0), seed_hi),
        "coincident_plate_boundary": ((0.0, *seed_lo[1:]), seed_hi),
    }
    refusals = {}
    for name, box in replacements.items():
        try:
            make_raised_seed(replace(intent, seed=replace(intent.seed, bounds_m=box)))
        except ValueError as error:
            refusals[name] = str(error)
    require(len(refusals) == len(replacements), "invalid merged solid reached construction")
    return refusals


def linked(intent):
    built = make_raised_seed(intent)
    generated_headers = built.headers()
    raw_headers = tuple(WriteHeadGraph(node, 19000) for node in generated_headers[:2])
    headers = tuple(ReadHeaderGraph(raw, 19000) for raw in raw_headers)
    cmgr_raw = WriteCmgrMut(built.system.ManagerValue, 19000)
    cmgr = ReadCmgrMut(cmgr_raw, 19000)
    config_raw, config = WriteConfigMut(built.system.RootValue, 19000, generated_headers[0])
    read_config = ReadConfigMut(config_raw, 19000, headers[0])
    link = MakeLinkContext(read_config, cmgr)
    raw, emitted = WriteResolMut(built.roots, None, 19000, config.MapValue, link)
    resolved = ReadResolvedMut(raw, 19000, read_config.MapValue, link)
    replay, replayed = WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000, read_config.MapValue, link)
    require(raw == replay and resolved.MapValue == replayed.MapValue
            and emitted.MapValue.CounterValue == resolved.MapValue.CounterValue
            and WriteConfigMut(read_config.RootValue, 19000, headers[0])[0] == config_raw
            and WriteCmgrMut(cmgr.RootValue, 19000) == cmgr_raw
            and tuple(WriteHeadGraph(node, 19000) for node in headers) == raw_headers,
            "generated seed archive maps or five owned streams changed under exact typed replay")
    values = NativeLink(read_config, resolved, "Config-0", "Config-0-ResolvedFeatures")
    streams = {"Config-0": config_raw, "Config-0-ResolvedFeatures": raw, "CMgr": cmgr_raw,
               "Config-0-ModelHeader": raw_headers[0], "Header2": raw_headers[1]}
    return values, headers, streams


def main():
    from hashlib import sha256

    for encoding in ("utf-16-le", "utf-8", "latin-1"):
        lookup(encoding)
    request = json.load(sys.stdin)
    audit.BeginBuild()
    intent = read_intent(request)
    link, headers, streams = linked(intent)
    result = observe(link, intent, headers)
    result.update(bad_input=invalid_geometries(intent), bad_readback=altered_owner_refusals(link, intent, headers),
                  map_counters=[link.ConfigValue.MapValue.CounterValue, link.ResolvedValue.MapValue.CounterValue],
                  streams={name: {"bytes": len(raw), "sha256": sha256(raw).hexdigest()} for name, raw in streams.items()},
                  guarded_runtime_reads=len(audit.DeniedReads), native_files_written=0)
    print(json.dumps(result, allow_nan=False, sort_keys=True))


if __name__ == "__main__":
    main()
