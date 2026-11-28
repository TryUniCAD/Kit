from argparse import ArgumentParser
from base64 import b64encode
from codecs import lookup
from dataclasses import replace
from pathlib import Path
from subprocess import run
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
SOURCES = ROOT / "re/tooling/sw2026"
sys.path[:0] = [str(path) for path in (ROOT, ROOT / "src", SOURCES, SOURCES / "serial", HERE.parent)]
BASE = "2f4a5cfc9c78bd7b2b8429d11cecec6eae59c796"

from ProveChamferDrivers import canonical, digest, model_requests, require


def key(value):
    fields = value.FieldsValue
    return value.ClassValue.NameValue, fields.get("f38"), fields.get("f3c")


def check_owners(feature, atom, root, *, expected_file=None, cold):
    fields = feature.FieldsValue
    base = fields["f888"].FieldsValue["items"][0]["o"]
    other = fields["f8a8"]
    edge, distinct = (item.FieldsValue["fe8"] for item in (base, other))
    keeper = fields["f880"]
    (retained,) = keeper["ff0"]["items"]
    require(keeper["ff0"]["n"] == 1 and retained["o"] is edge and edge is not distinct
            and base is not other and base.FieldsValue["f58"] is not other.FieldsValue["f58"]
            and (edge.FieldsValue["f70"] == 0 if cold else edge.FieldsValue["f70"] > 0),
            "chamfer keeper must alias the sole selected edge and preserve independent component identities")
    for entry in (base, other):
        check = entry.FieldsValue
        require(check["f18"] == check["f1c"] == atom.FieldsValue["f140"]
                and check["f58"].FieldsValue["owner"] is root and check["ff0"] is None and check["n140"] == 0,
                "selected element points outside the actual local part and atom")
    require(distinct.FieldsValue["f70"] == 0 and all(
        row.FieldsValue["f08"] == len(row.FieldsValue["f10"]) == 4 and row.FieldsValue["fe8"] == 0x200
        for row in (edge, distinct)), "ordinary selected edge has unexpected identity or role count")
    support, detached = (tuple(item["f08"] for item in ref.FieldsValue["f10"]) for ref in (edge, distinct))
    result = tuple(item["id"]["f08"] for item in keeper["f18"]["items"])
    require(tuple(map(key, support)) == tuple(map(key, detached)) and len(set(support + detached + result)) == 10
            and keeper["f18"]["n"] == len(result) == 2
            and tuple(map(key, result)) == (("moSurfaceIdRep_c", None, None), ("moFilletSurfIdRep_c", 1, None))
            and all(record.FieldsValue["f10"]["f08"] is feature for record in result)
            and all(record.FieldsValue["f10"]["f08"] is None for record in support + detached),
            "surface representation graph lost its ordered clone or direct result-owner roles")
    references = tuple(item.FieldsValue["f10"]["f10"] for item in support + detached + result)
    file = references[0].FieldsValue["f08"]
    require(len(set(references)) == 10 and all(ref.FieldsValue["f08"] is file for ref in references)
            and (expected_file is None or file is expected_file),
            "history references must retain their own events and one actual self-file owner")
    branches = [ref.FieldsValue["f10"] for ref in references]
    require(all(item == branches[0] for item in branches[:8])
            and all(item == branches[-1] for item in branches[-2:])
            and branches[0]["f00"] == atom.FieldsValue["f12c"]
            and branches[-1]["f00"] == atom.FieldsValue["f130"] == fields["f08"],
            "stock and result references have a mismatched producer or event")
    return support, (branches[0]["f08"], branches[-1]["f08"]), file


def check_source(folder, name, phase):
    from AuditTypedChamfer import (
        KPartitionStream, ReadActiveNodes, ReadBodyTree, ReadChmfOwn, ReadXmtStages, RequireXmt,
        SldprtArchive, DecodePartData, expected_inputs, guard_runtime, link_archive, owners_and_surfaces, predict,
    )
    from FilletHistoryBody import edge_incidence, point_set_match, selected_support
    from LinkChamferGraph import write_roots

    data, case, _, _ = expected_inputs(folder, name, phase == "edited")
    denied = guard_runtime()
    archive = SldprtArchive.from_bytes(data)
    link, headers, context = link_archive(archive)
    owned = ReadChmfOwn(link)
    source = link.ResolvedValue
    emitted, encoded = write_roots(source.RootsValue, source.ExtraFields, link.ConfigValue.MapValue, context)
    require(emitted == archive.require(link.StreamName) and encoded == source.MapValue,
            "scoped shared emitter changed native resolved bytes or aliases")
    prior = owned.StockValue.FieldsValue["f4a8"]
    chooser = prior["f48"]["items"][0]["o"]
    first = chooser.FieldsValue["f08"]["items"][0]["o"]
    earlier_file = first.FieldsValue["f10"][0]["f08"].FieldsValue["f10"]["f10"].FieldsValue["f08"]
    supports, stamps, _ = check_owners(owned.FeatureValue, owned.AtomValue, link.ConfigValue.RootValue,
                                       expected_file=earlier_file, cold=False)
    active, history = DecodePartData(archive.require(KPartitionStream), KPartitionStream)
    stages = ReadXmtStages(history.data, ReadActiveNodes(active.data), tuple(mark["f18"] for mark in owned.Controllers))
    previous = stages[1].NodesValue
    tree, endpoints = ReadBodyTree(previous), predict(case)["source_edge"]
    (edge_index,) = (index for index in tree.EdgeIds
                     if point_set_match(edge_incidence(previous, index)[0], endpoints))
    edge = RequireXmt(previous, edge_index, 16)
    first = RequireXmt(previous, edge.Integer("halfedge"), 17)

    def other(fin):
        paired = RequireXmt(previous, fin.Integer("other"), 17)
        require(paired.Integer("other") == fin.IndexValue, "rollback fin is not reciprocal")
        return paired

    def face(fin):
        return RequireXmt(previous, fin.Integer("loop"), 15).Integer("face")

    positive = first if first.FieldsValue["sense"] == "+" else other(first)
    roles = (face(positive), face(other(positive)),
             *(face(other(RequireXmt(previous, positive.Integer(key), 17))) for key in ("backward", "forward")))
    reps, _, epochs = owners_and_surfaces(link, owned, headers)
    readback = selected_support(previous, tree, endpoints, owned.StockValue["f08"], epochs[owned.StockValue["f08"]], reps)
    expected = tuple(row["face_slot"] for row in readback["faces_in_archive_order"])
    require(roles == expected and prior["f68"] is owned.StockValue and not denied,
            "physical positive-fin order or earlier chooser ownership changed")
    words = owned.FeatureValue.FieldsValue["f8c8"]
    require(words["n"] == len(words["items"]), "saved options lost their typed framing")
    return {"source_sha256": digest(data), "case": name, "phase": phase, "resolved_sha256": digest(emitted),
            "resolved_bytes": len(emitted), "mapped_roots": len(source.RootsValue), "map_frontier": encoded.CounterValue,
            "positive_fin_faces": roles, "surface_keys": list(map(key, supports)), "creation_epochs": stamps,
            "expected_direct_result_and_earlier_file_aliases": True, "edge_handle": owned.SelectedRef["f70"],
            "saved_options_observed": [item["v"] for item in words["items"]], "guarded_runtime_reads": len(denied)}


def check_model(*, deliver=False):
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

    audit = BuildAudit(SOURCES / "serial/defs")
    sys.addaudithook(audit.InspectEvent)
    from LinkChamferGraph import build_graph, emit_cold, write_roots
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Container.Format import KPartitionStream, KResolvedFeaturesStream
    from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfDim import ReadChmfDim
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
    from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
    from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
    from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import MakePlainDoc

    tuple(lookup(codec) for codec in ("ascii", "utf-8", "utf-16-le", "latin-1", "cp1252"))
    input_bytes = sys.stdin.buffer.read()
    request = json.loads(input_bytes)
    audit.BeginBuild()
    stock = MakePlainDoc(request["case"], *request["size_mm"])
    stock = replace(stock, configurations=(replace(stock.configurations[0], name="Default"),),
                    sketches=(replace(stock.sketches[0], name="ChamferStockSketch"),),
                    feature_timeline=(replace(stock.feature_timeline[0], name="ChamferStockBoss"),),
                    bodies=(replace(stock.bodies[0], name="ChamferStockBoss"),))
    candidate, bevel, atom, drivers, shape, file = build_graph(stock, request)
    prior, = (value for value in candidate.ResolvedValue.RootsValue if value is candidate.BossValue.FeatureValue)
    roots = candidate.ResolvedValue.RootsValue + (bevel,)
    check_owners(bevel, atom, candidate.SystemValue.RootValue, expected_file=file, cold=True)
    raw, streams, config_counter, terminal = emit_cold(candidate, bevel, drivers)
    archive = SldprtArchive.from_bytes(raw)
    require(KPartitionStream not in archive.streams and all(archive.require(key) == value for key, value in streams.items()),
            "fresh cold container must preserve all model-computed streams and omit the solved partition")
    link = ReadNativeLink(archive, 0, ReadChamfers=True)
    read, resolved = link.ConfigValue, link.ResolvedValue
    forward, replay_map = write_roots(
        resolved.RootsValue, resolved.ExtraFields, read.MapValue, resolved.ContextValue)
    require(forward == archive.require(KResolvedFeaturesStream) and replay_map == resolved.MapValue
            and read.MapValue.CounterValue == config_counter and replay_map.CounterValue == terminal
            and WriteConfigMut(read.RootValue, 19000, read.HeaderValue)[0] == archive.require("Contents/Config-0")
            and resolved.ExtraFields == {"n": 0, "fcd8": []}
            and [item.ClassValue for item in resolved.RootsValue] == [item.ClassValue for item in roots],
            "scoped map or linked streams changed during complete insertion")
    previous, shown = resolved.RootsValue[-2:]
    inherited_atom = read.RootValue.FieldsValue["fd88"]["atoms"][0]["o"]
    require(previous.FieldsValue["f08"] == prior.FieldsValue["f08"]
            and previous.FieldsValue["f528"]["items"][0]["o"] is inherited_atom is shown.FieldsValue["f538"]
            and shown.FieldsValue["f8c8"] == {"n": 0, "items": []},
            "linked chamfer rewired the inherited stock body")
    faces, stamps, _ = check_owners(shown, inherited_atom, read.RootValue, cold=True)
    observed = tuple(ReadChmfDim(link, shown.FieldsValue[owner], angular)
                     for owner, angular in (("f810", False), ("f818", True)))
    dim_ids = tuple(driver.DimensionNode.FieldsValue["f50"] for driver in observed)
    require(tuple(item.NameValue for item in observed) == ("D1", "D2")
            and tuple(item.ValueSi for item in observed) == (request["shape"]["distance_m"], request["shape"]["angle_rad"])
            and dim_ids == tuple(item.DimensionValue.FieldsValue["f50"] for item in drivers)
            and dim_ids[0] < dim_ids[1] < shown.FieldsValue["f08"] and not audit.DeniedReads,
            "generated model lost its actual local values, ID order or runtime purity")
    refusals = []
    input_shape = request["shape"]
    for contrast, changed, text in (
        ("foreign_body", {"body_id": "foreign/body"}, "actual modeled stock body"),
        ("contradicted_bounds", {"stock_bounds_m": [[-0.04, 0.025], [-0.09, 0.05], [0.0, 0.034]]},
         "actual generated blind boss"),
        ("longitudinal_distance_side", {"distance_axis": input_shape["edge_axis"]},
         "distance must be assigned to one transverse stock side"),
    ):
        try:
            build_graph(stock, request | {"shape": input_shape | changed})
        except ValueError as error:
            require(text in str(error), "unexpected refusal for " + contrast + ": " + str(error))
            refusals.append(contrast)
        else:
            raise ValueError(contrast + " reached emitted graph")
    try:
        ReadNativeLink(archive, 0)
    except ValueError as error:
        require("unsupported SOLIDWORKS body class Chamfer_c schema 1" in str(error),
                "normal reader refused at the wrong guard")
        refusals.append("default_reader_closed")
    else:
        raise ValueError("ordinary registry unexpectedly admitted the fresh research subtype")
    require(not audit.DeniedReads, "a failed scoped conversion attempted external access")
    row = {"case": request["case"], "intent_sha256": digest(input_bytes), "container_sha256": digest(raw),
            "bytes": len(raw), "roots_before": len(roots) - 1, "roots_after": len(roots),
            "config_seed": config_counter, "terminal_map": terminal,
            "streams": {key: {"bytes": len(value), "sha256": digest(value)} for key, value in streams.items()},
            "face_roles": list(map(key, faces)), "selected_endpoints_m": shape.endpoints, "epochs": stamps,
            "feature_id": shown.FieldsValue["f08"], "dimension_ids": dim_ids,
            "rejection_reasons": refusals, "guarded_runtime_reads": len(audit.DeniedReads)}
    if deliver:
        row["model_bytes"] = b64encode(raw).decode("ascii")
    return row


def invoke(*arguments, data=None):
    result = run((sys.executable, "-I", "-B", str(HERE), *arguments), input=data, capture_output=True,
                 check=False, timeout=60)
    require(result.returncode == 0 and not result.stderr, result.stderr.decode())
    return result.stdout


def composed_requests():
    for index, request in enumerate(model_requests()):
        if index == 0:
            request["presentation"].update(view="*Front", distance_text=[1.375, .009], angle_text_xy_m=[0.0, -.01225])
            request["catalog"][0] = {"name": "*Front", "basis": ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))}
            request["shape"]["corner"] = {"0": 1, "1": 1}
        size = (77.125 - 10 * index, 40.625 + 11 * index, 38.875 - 7 * index)
        x, y, z = (value / 1000 for value in size)
        request["shape"].update(body_id="body/boss", stock_bounds_m=[[-x/2, x/2], [-y/2, y/2], [0.0, z]])
        case = request["case"]
        yield {"case": case, "catalog": request["catalog"], "shape": request["shape"],
               "presentation": request["presentation"], "size_mm": size, "feature": "DistanceAngleEdgeChamfer",
               "epoch": 1795471200 + index * 61, "locator": rf'C:\KitGeneratedChamfer01\Packet\Candidates\{case}.SLDPRT'}


def comparison(folder, output):
    models = []
    for request in composed_requests():
        data = canonical(request)
        first, second = (invoke("--model", data=data) for _ in range(2))
        require(first == second, "guarded chamfer insertion differed across interpreters")
        models.append(json.loads(first))
    names = ("ChamferDistanceAxialA", "ChamferAngleTopB")
    native = [json.loads(invoke("--source", str(folder), name, phase))
              for name in names for phase in ("original", "edited")]
    require(len({row["container_sha256"] for row in models}) == 2
            and len({row["streams"]["Contents/Config-0-ResolvedFeatures"]["bytes"] for row in models}) == 2
            and all(len(row["saved_options_observed"]) == 6 for row in native)
            and len({tuple(row["saved_options_observed"]) for row in native}) == 1,
            "source fields and independent archive lengths did not discriminate")
    tool_hashes = {path.name: digest(path.read_bytes()) for path in
                   (HERE, HERE.with_name("ChamferEdgeOwners.py"), HERE.with_name("LinkChamferGraph.py"))}
    result = {"revision_base": BASE, "tool_sha256": tool_hashes, "guarded_model_processes": 4,
              "guarded_source_processes": 4, "generated_containers_in_memory": models, "disclosed_source_replay": native,
              "persistent_native_files_written": 0, "native_processes": 0, "heldout_credit": 0}
    require(not output.resolve().is_relative_to(folder.resolve()), "receipt cannot modify source custody")
    with output.open("xb") as stream:
        stream.write(canonical(result))
    return {"output_sha256": digest(output.read_bytes()), "guarded_model_processes": 4, "guarded_source_processes": 4}


if __name__ == "__main__":
    parser = ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--model", action="store_true")
    mode.add_argument("--source", nargs=3)
    mode.add_argument("--compare", nargs=2, type=Path)
    parser.add_argument("--deliver", action="store_true")
    args = parser.parse_args()
    require(not args.deliver or args.model, "native payload may leave only a neutral worker")
    result = check_model(deliver=args.deliver) if args.model else check_source(Path(args.source[0]), *args.source[1:]) if args.source else comparison(*args.compare)
    sys.stdout.buffer.write(canonical(result))
