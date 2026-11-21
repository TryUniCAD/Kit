from argparse import ArgumentParser
from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
import json
from math import dist, isclose, tan
from pathlib import Path
from struct import pack
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent / "edge_fillet_source"))

from AuditFilletArchive import (
    CONFIG, RESOLVED, VERSION, checked, checked_json, digest, guard_runtime, registry, require,
)
from ChamferModel import predict, validate_spec, values_si
from Core import ArchiveMap, Obj
from FilletArchiveKernel import active_replay
from FilletArchiveOwners import signature, span, stock_epoch, surface
from FilletHistoryBody import body_tracking, face_endpoint_hits, point_set_match, selected_support, vertex_point
from ResolvedBridge import MBSM, make_node
from Streams import StreamDoc
from defs.ResolvedCore import store_resolved_state_compat

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Partition.History.ReadXmtStages import ReadXmtStages
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import ReadBodyAttrs
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyFaces import ReadBodyFaces
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyLoop import ReadBodyLoop
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyTree import ReadBodyTree
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfOwn import ReadChmfOwn
from convert.adapters.solidworks.Core.TypedResolved.Fillets.CheckFilletDeps import CheckFilletDeps
from convert.adapters.solidworks.Core.TypedResolved.Fillets.CheckFilletUndo import CheckFilletUndo
from convert.adapters.solidworks.Core.TypedResolved.Fillets.ReadFilletSlot import ReadFilletSlot
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import CheckTreeAlias
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.CheckRevSelf import CheckRevSelf
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.RevFaceRef import RevFaceRef
from convert.Geometry.Parasolid import DecodePartData

LOCK = "a696a97d73129ef7ffd7e829dfff7d1729000309e1273c0bef70b5f2ceedddb8"
NAMES = ("ChamferDistanceAxialA", "ChamferAngleTopB")
CONTROLS = {
    "ControlRectangle": "31f880dd18a009e6e2cdc5c666484d02f50c7b2117f50051e071cad5d9f21b4f",
    "ControlCircle": "ee3d82b60adef1a7688fd0e6086d797f8c956c41e070670a581ad8669c9c35b7",
}
DEFAULT_REFUSAL = "unsupported SOLIDWORKS body class Chamfer_c schema 1"
PRODUCTION = ROOT / "src/convert/adapters/solidworks"
FIXED_IMPLEMENTATION_PATHS = (
    PRODUCTION / "Archive/Bodies/Layouts/Resolved/Chamfers/ChamferFields.py",
    PRODUCTION / "Archive/Resolved/ReadResolvedMut.py",
    PRODUCTION / "Archive/Resolved/UseChmfCtxMut.py",
    PRODUCTION / "Core/TypedResolved/ReadNativeLink.py",
)


def refuse(action, message):
    try:
        action()
    except ValueError as error:
        require(str(error) == message, f"unexpected chamfer boundary: {error}")
        return message
    raise ValueError(f"missing chamfer refusal: {message}")


@contextmanager
def altered(fields, key, value):
    previous = fields[key]
    fields[key] = value
    try:
        yield
    finally:
        fields[key] = previous


def contrast(link, owners, config, context, resolved):
    node = owners.FeatureValue.FieldsValue
    with altered(node, "f8a0", 99):
        mode = refuse(lambda: ReadChmfOwn(link), "unsupported ordinary SOLIDWORKS chamfer mode or selector")
    with altered(node["f880"]["ff0"]["items"][0], "o", owners.DetachedRef):
        alias = refuse(lambda: ReadChmfOwn(link), "ordinary chamfer has conflicting selected edge ownership")
    with altered(node["f8a8"].FieldsValue, "f18", owners.AtomValue.FieldsValue["f140"] + 1):
        other_body = refuse(lambda: ReadChmfOwn(link), "ordinary chamfer has conflicting selected edge ownership")
    cache = owners.AngleValue.DisplayNode.FieldsValue["f5b0"]
    with altered(cache, "data", pack("<d", owners.AngleValue.ValueSi + 0.125)):
        driver = refuse(lambda: ReadChmfOwn(link), "ordinary chamfer display differs from its live driver")
    refuse(lambda: ReadResolvedMut(resolved, VERSION, config.MapValue, context | {"cmgr_f658": 0}, ReadChamfers=True),
           "unsupported ordinary SOLIDWORKS chamfer archive context")
    refuse(lambda: ReadResolvedMut(resolved, VERSION, config.MapValue, context, ReadChamfers=True, ReadFillets=True),
           "SOLIDWORKS resolved edge finish scopes are exclusive")
    headers = config.HeaderValue, config.HeaderValue
    source_key = owners.SelectedRef["f10"][0]["f08"]["f10"]["f10"]["f10"]
    with altered(source_key, "f08", source_key["f08"] + 1):
        stale_event = refuse(lambda: owners_and_surfaces(link, owners, headers), "fillet surface has a different producer event")
    return {"unknown_mode": mode, "crossed_keeper": alias, "foreign_atom": other_body,
            "stale_angle_cache": driver, "alternate_context": True, "exclusive_edge_finish_context": True,
            "foreign_support_creation_event": stale_event}


def owners_and_surfaces(link, owners, headers):
    stock, feature, selected, detached = owners.StockValue, owners.FeatureValue, owners.SelectedRef, owners.DetachedRef
    epochs = stock_epoch((stock, feature), *headers)
    field = feature.FieldsValue["f880"]
    keeper = [item["id"]["f08"] for item in field["f18"]["items"]]
    require(field["f18"]["n"] == len(keeper) == 2
            and [item.cls for item in keeper] == ["moSurfaceIdRep_c", "moFilletSurfIdRep_c"]
            and all(item["f10"]["f08"] is feature for item in keeper), "chamfer keeper does not own the actual output feature")
    selected_rows, detached_rows = [[item["f08"] for item in ref["f10"]] for ref in (selected, detached)]
    typed = []
    for item in selected_rows + detached_rows:
        ref = item["f10"]["f10"]
        typed.append(RevFaceRef(item, ref["f08"], ref["f10"]["f00"], item.cls == "moEndFaceSurfIdRep_c", item["f38"]))
    require(len({item.Representation for item in typed}) == 8, "separate chamfer edge refs alias surface representations")
    CheckTreeAlias(link, tuple(item for row in typed for item in (row.Representation, row.ExternalValue)))
    for header in headers:
        CheckRevSelf(header, typed)
    primary, secondary = [[surface(item, epochs) for item in rows] for rows in (selected_rows, detached_rows)]
    keepers = [surface(item, epochs) for item in keeper]
    require(signature(primary) == signature(secondary) and all(row["feature_id"] == stock["f08"] for row in primary)
            and all(row["feature_id"] == feature["f08"] for row in keepers)
            and selected["f70"] > 0 == detached["f70"]
            and all(ref["fe8"] == 512 and ref["f60"] == 1 and ref["f64"] == ref["f48"] == 0 and ref["fec"] == VERSION
                    for ref in (selected, detached)), "chamfer picked and detached references disagree on actual ordered support")
    return primary, keepers, epochs


def bevel_legs(previous, support, vertices, stock, owners):
    axis = stock["edge_axis"]
    source = [value for index, value in enumerate(stock["source_edge"][0]) if index != axis]
    distance, angle = owners.Distance.ValueSi, owners.AngleValue.ValueSi
    values = []
    for support_row, expected in zip(support["faces_in_archive_order"][:2], (distance * tan(angle), distance), strict=True):
        face = RequireXmt(previous, support_row["face_slot"], 14)
        hits = face_endpoint_hits(previous, face, vertices)
        measured = [dist(source, [value for index, value in enumerate(vertices[point]) if index != axis]) for point in hits]
        require(len(hits) == 2 and all(isclose(value, expected, abs_tol=1e-11) for value in measured),
                "actual chamfer legs disagree with the ordered incident-face and distance rule")
        values.append(measured)
    return values


def physical(archive, owners, matched, representations, keepers, epochs, case):
    active, history = DecodePartData(archive.require(KPartitionStream), KPartitionStream)
    require((active.kind, history.kind) == ("partition", "deltas")
            and active.schema == history.schema == "SCH_3701250_37102_13006", "unsupported chamfer kernel context")
    nodes = ReadActiveNodes(active.data)
    selectors = tuple(mark["f18"] for mark in owners.Controllers)
    stages = ReadXmtStages(history.data, nodes, selectors)
    CheckFilletDeps(stages)
    previous = stages[1].NodesValue
    live_body, live_name = ReadFilletSlot(nodes, owners.AtomValue, owners.FeatureValue)
    stock_body, stock_name = ReadFilletSlot(previous, owners.AtomValue, owners.StockValue)
    CheckFilletUndo(stages, live_body, stock_body, live_name, stock_name)
    tree = ReadBodyTree(previous)
    stock = predict(case)
    require(tree.BodyIndex == stock_body.IndexValue
            and point_set_match(tuple(vertex_point(previous, idx) for idx in tree.VertexIds), stock["vertices"]),
            "restored chamfer stock vertices differ from basic authored stock")
    producer = owners.StockValue["f08"]
    support = selected_support(previous, tree, stock["source_edge"], producer, epochs[producer], representations)
    faces = [RequireXmt(nodes, idx, 14) for idx in ReadBodyFaces(nodes, live_body, 7)]
    emitted_key = (72, owners.FeatureValue["f08"], epochs[owners.FeatureValue["f08"]], 0, keepers[1]["f38"])
    result = [face for face in faces if RequireXmt(
        nodes, ReadBodyAttrs(nodes, face)["FACE_ID_2001"].Indexes("fields")[2], 82
    ).Indexes("values") == emitted_key]
    require(len(result) == 1 and all(RequireXmt(nodes, face.Integer("surface"), 50) for face in faces),
            "result chamfer face does not match its own keeper lineage")
    bevel = result[0]
    _, fins = ReadBodyLoop(nodes, bevel)
    vertices = tuple(vertex_point(nodes, nodes[index].Integer("vertex")) for index in fins)
    require(point_set_match(vertices, matched["bevel_vertices"]), "physical bevel vertices disagree with the measured analytic branch")
    require(point_set_match(tuple(vertex_point(nodes, idx) for idx, item in nodes.items() if item.KindValue == 18), matched["vertices"])
            and sum(item.KindValue == 16 for item in nodes.values()) == 15, "physical shape differs from the independent analytic clip")
    # the first undo must actually revive the selected pre-chamfer edge
    chosen = RequireXmt(previous, support["edge_slot"], 16)
    undo = stages[0].UndoValue
    require(any(chosen is item for item in undo.RestoredValue) and chosen.IndexValue not in nodes,
            "selected chamfer edge is not restored by its actual undo")
    return {
        "body_slot": live_body.IndexValue, "actual_stock_tracking": body_tracking(previous, stock_body),
        "actual_live_tracking": body_tracking(nodes, live_body), "stock_support": support,
        "selected_edge_endpoints_m": stock["source_edge"], "result_face_slot": bevel.IndexValue,
        "bevel_legs_on_incident_faces_m": bevel_legs(previous, support, vertices, stock, owners),
        "result_face_attribute": emitted_key,
        "kernel_stages": [{"mark": stage.MarkValue.Integer("id"), "nodes": len(stage.NodesValue)}
                          for stage in stages],
        "selected_undo": {"restored": len(undo.RestoredValue), "removed": len(undo.RemovedValue),
                          "previous": len(undo.PreviousValue), "capacity": undo.CopyCapacity},
        "active_replay": active_replay(active.data, {
            index: replace(node, FieldsValue={"values": node.FieldsValue["values"].decode("ascii")})
            if node.KindValue == 84 else node for index, node in nodes.items()
        }),
        "partition_sha256": digest(archive.require(KPartitionStream)),
        "history_sha256": history.sha256,
    }


def expected_inputs(folder, name, edited):
    lock = checked_json(folder / "DisclosedSourceLock.json", LOCK)
    require(lock["passed"] and lock["cohort"] == "disclosed" and lock["distinct_processes"] == 8
            and lock["writer_output_count"] == 0 and all(row["passed"] for row in lock["controls"].values()),
            "disclosed source lock is not a passing native lifecycle")
    cases = validate_spec(checked_json(HERE / "DisclosedChamferInputs.json", lock["spec_sha256"]))
    idx = NAMES.index(name)
    row = lock["sources"][idx]
    require(cases[idx]["name"] == name and row["slot"] == idx and row["passed"], "incorrect disclosed case")
    stem = name + ("Edited" if edited else "") + ".SLDPRT"
    data = checked(folder / "DisclosedModels" / stem, row["edited_sha256" if edited else "original_sha256"])
    phase = row["phases"][2 if edited else 1]["receipt_sha256"]
    return data, cases[idx], tuple(row["orientation"]), phase


def link_archive(archive):
    headers = tuple(ReadHeaderGraph(archive.require(name), VERSION) for name in (CONFIG + "-ModelHeader", "Header2"))
    config = ReadConfigMut(archive.require(CONFIG), VERSION, headers[0], NodeMaker=make_node)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), VERSION)
    context = MakeLinkContext(config, manager)
    resolved = ReadResolvedMut(archive.require(RESOLVED), VERSION, config.MapValue, context, NodeMaker=make_node, ReadChamfers=True)
    return NativeLink(config, resolved, CONFIG, RESOLVED), headers, context


def inspect(data, case, branch, edited, phase, reg):
    archive = SldprtArchive.from_bytes(data)
    actual = ReadChmfOwn(ReadNativeLink(archive, 0, ReadChamfers=True))
    link, headers, context = link_archive(archive)
    config, resolved = link.ConfigValue, link.ResolvedValue
    owners = ReadChmfOwn(link)
    observed = owners.Distance.ValueSi, owners.AngleValue.ValueSi
    require(observed == values_si(case, edited) == (actual.Distance.ValueSi, actual.AngleValue.ValueSi)
            and not ReadParents(owners.FeatureValue), "chamfer source driver or native root role differs")
    proof = resolved.ReportValue
    cells = [row["typed_values"][0] for row in proof["native_byte_fields"] if row["schema"] == "dm.FUN_4bd03960"]
    require(proof["completed"] and not proof["missing_schemas"] and not proof["provisional_schemas"]
            and cells == [case["size_mm"][2] / 1000, *observed], "typed display cell inventory differs")
    saved_config, seed = WriteConfigMut(config.RootValue, VERSION, config.HeaderValue)
    doc = StreamDoc("resolved", {"base": resolved.MapBase, "n": len(resolved.RootsValue), "context": context,
                                 "mbsm": Obj(MBSM, resolved.ExtraFields)}, list(resolved.RootsValue))
    replay, replay_map = store_resolved_state_compat(doc, reg, VERSION, seed=ArchiveMap(snapshot=seed.MapValue))
    require(saved_config == archive.require(CONFIG) and replay == archive.require(RESOLVED)
            and replay_map.count == resolved.MapValue.CounterValue == 325 and resolved.MapBase == 110,
            "linked production reader does not replay exactly through the research codec")
    reps, keepers, epochs = owners_and_surfaces(link, owners, headers)
    shape = physical(archive, owners, predict(case, observed, branch), reps, keepers, epochs, case)
    refusals = {"default_read": refuse(lambda: ReadNativeLink(archive, 0), DEFAULT_REFUSAL),
                "default_store": refuse(lambda: WriteResolMut(
                    resolved.RootsValue, resolved.ExtraFields, VERSION, seed.MapValue, context), DEFAULT_REFUSAL)}
    if not edited:
        refusals |= contrast(link, owners, config, context, archive.require(RESOLVED))
    drivers = [{"name": driver.NameValue, "value_si": driver.ValueSi, "dimension_id": driver.DimensionNode["f50"],
                "owners": [NativeNodeSpan(link, item) for item in (driver.DisplayNode, driver.HandleNode,
                             driver.DimensionNode, driver.ParameterNode)]}
               for driver in (owners.Distance, owners.AngleValue)]
    return {"source_sha256": digest(data), "native_phase_sha256": phase, "case": case["name"], "edited": edited,
            "maps": [resolved.MapBase, resolved.MapValue.CounterValue], "exact_linked_replay": True,
            "config_sha256": digest(saved_config), "resolved_sha256": digest(replay), "resolved_bytes": len(replay),
            "schema_count": len(proof["used_schemas"]), "feature": span(owners.FeatureValue), "drivers": drivers,
            "selected_ref": span(owners.SelectedRef), "detached_ref": span(owners.DetachedRef),
            "selected_f70": owners.SelectedRef["f70"], "detached_f70": owners.DetachedRef["f70"],
            "ordered_support": reps, "keeper_result_providers": keepers, "physical": shape, "refusals": refusals}


def control(root, name):
    raw = checked(root / "re/solidworks/v2026/corpus/curves-discovery" / (name + ".SLDPRT"), CONTROLS[name])
    denied = guard_runtime()
    archive = SldprtArchive.from_bytes(raw)
    default = ReadNativeLink(archive, 0)
    scoped = ReadNativeLink(archive, 0, ReadChamfers=True)
    for link in (default, scoped):
        config, seed = WriteConfigMut(link.ConfigValue.RootValue, VERSION, link.ConfigValue.HeaderValue)
        data, _ = WriteResolMut(link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields, VERSION,
                                seed.MapValue, link.ResolvedValue.ContextValue)
        require(config == archive.require(CONFIG) and data == archive.require(RESOLVED), "unchanged control lost typed replay")
    require(default.ResolvedValue.ReportValue == scoped.ResolvedValue.ReportValue and not denied,
            "unused chamfer opt-in changed the prior control")
    return {"control": name, "source_sha256": digest(raw), "same_default_and_opt_in": True, "guarded_external_reads": len(denied)}


def launch(*args):
    result = subprocess.run((sys.executable, "-E", "-B", str(Path(__file__).resolve()), *args),
                            capture_output=True, text=True, check=False, timeout=40)
    require(result.returncode == 0 and not result.stderr, f"guarded chamfer process failed: {result.stderr}")
    return json.loads(result.stdout)


def main():
    parser = ArgumentParser(description="Bind typed chamfer archive fields and rollback to disclosed 2026 stock and edited drivers")
    parser.add_argument("--folder", type=Path)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--report", type=Path)
    modes.add_argument("--phase", nargs=2)
    modes.add_argument("--control", choices=CONTROLS)
    args = parser.parse_args()
    if args.control:
        row = control(ROOT, args.control)
    elif args.phase:
        name, phase = args.phase
        require(name in NAMES and phase in ("original", "edited"), "choose one exact disclosed phase")
        edited = phase == "edited"
        data, case, branch, native_phase = expected_inputs(args.folder, name, edited)
        reg = registry()
        denied = guard_runtime()
        row = inspect(data, case, branch, edited, native_phase, reg)
        require(not denied, "guarded chamfer process attempted external access")
        row["guarded_external_reads"] = 0
    else:
        require(args.folder.is_absolute() and not args.report.resolve().is_relative_to(args.folder.resolve()),
                "source custody and output must be separate")
        before = launch("--control", "ControlRectangle")
        rows = [launch("--folder", str(args.folder), "--phase", case, phase)
                for case in NAMES for phase in ("original", "edited")]
        after = launch("--control", "ControlCircle")
        row = {"schema": "kit.sw2026.edge-chamfer-typed-bounded-read.v1",
               "baseline_revision": "e9d034f5bede62142e91383e5a181098904a88db",
               "implementation_sha256": {
                   path.relative_to(ROOT).as_posix(): digest(path.read_bytes())
                   for path in (*FIXED_IMPLEMENTATION_PATHS, *sorted((PRODUCTION / "Core/TypedResolved/Chamfers").glob("*.py")),
                                Path(__file__).resolve())
               },
               "disclosed_lock_sha256": LOCK, "passed": True, "native_launches": 0, "guarded_processes": 6,
               "disclosed_parts": rows, "archive_controls": [before, after],
               "private_sources_read": 0, "writer_output_count": 0}
        with args.report.open("x", encoding="utf-8") as stream:
            json.dump(row, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write("\n")
        row = {"passed": True, "receipt_sha256": sha256(args.report.read_bytes()).hexdigest(), "guarded_processes": 6}
    print(json.dumps(row, allow_nan=False))


if __name__ == "__main__":
    main()
