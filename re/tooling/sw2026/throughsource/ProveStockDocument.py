from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from pathlib import Path
from subprocess import check_output, run
import codecs
import json
import sys


HERE = Path(__file__).resolve()
REPO = HERE.parents[4]
BASE = "f815b77a27d78a3654f9e7c084ce0921c01f692a"
SELECTED = "748cdbec3fe61d6801f3d606e64fe42ecba95e9a647897be3fe3790570a889f3"
UNRESTRICTED = "f87568db0dfa361ea44c42def01063c8ed07ea57c8270098cf3c60995e3e3b22"
FORMAT = "solidworks.sldprt"
COMPATIBILITY = "multiple operation histories are outside typed blind topology"
NEGATIVES = {
    "detached-producer": "selected two stock timeline differs from its linked producers",
    "cross-datum": "selected two stock profile has alternate support or dimensions",
    "cross-depth": "independent stocks share an actual driving depth owner",
}
MODES = ("selected", "named", "no-brep", "raw", "unknown-config", "unrestricted", *NEGATIVES)
CORE = "src/convert/adapters/solidworks/Core"
TYPED = CORE + "/TypedResolved"
IMPLEMENTATION = (
    CORE + "/Adapter.py",
    TYPED + "/ProjectTyped.py",
    TYPED + "/Presentation/ProjectTree.py",
    TYPED + "/Presentation/RootOrder.py",
    TYPED + "/Cuts/WithCutSelection.py",
    *(TYPED + "/Cuts/MultiStock/" + name for name in (
        "BindStockDoc.py", "CheckStockProfs.py", "StockDesigns.py", "StockOpsMap.py",
        "StockTopCount.py", "TryStockPart.py", "Cache/ReadStockCache.py", "Cache/StockCacheGeom.py",
    )),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_document(document, cache):
    from interchange.Features.FeatureExtrude import ExtrudeFeature
    from interchange.geometry.Models.GeometryCurves import CircleGeometry, LineGeometry, PointGeometry

    require(document.source.sha256 == SELECTED and document.brep == cache.BrepValue, "active geometry or source changed")
    configurations = [[c.id, c.name, c.active] for c in document.configurations]
    require(configurations == [["sldprt:configuration:0", "Default", True]], "wrong neutral configuration")
    manager = document.metadata["solidworks.typed_configuration_manager"]
    manager_rows = manager["configurations"]
    require(manager["status"] == "complete" and len(manager_rows) == 1
            and manager_rows[0]["name"] == "Default" and manager_rows[0]["selected_by_f360"]
            and manager_rows[0]["selected_by_f368"], "actual manager selectors changed")
    typed = document.metadata["solidworks.typed_resolved_semantics"]
    require(typed["status"] == "supplemented" and typed["line_loop_profiles"] == (26, 33)
            and typed["free_circle_profiles"] == (41,) and typed["public_writer_qualified"] is False,
            "typed profile evidence changed")
    tree = typed["native_tree"]
    rows = [int(step.id.rsplit(":", 1)[1]) for step in document.feature_timeline]
    require(rows == [8, 23, 24, 25, 22, 7, 1, 17, 18, 10, 9, 21, 16, 11, 2, 3, 4, 5, 6, 12, 13, 14, 15,
                     19, 26, 32, 33, 40, 41, 47]
            and tuple(rows) == tree["retained_public_ids"] and len(tree["root_ids"]) == 23
            and len(tree["member_ids"]) == 6 and len(tree["configuration_helpers"]) == 1
            and not tree["full_native_tree_qualified"] and not document.diagnostics,
            "source tree retention changed")
    steps = document.feature_timeline[-6:]
    operations = []
    for step in steps[1::2]:
        value = step.definition
        require(isinstance(value, ExtrudeFeature), "operation lacks its editable extrusion definition")
        operations.append([step.id, step.name, str(step.operation), list(step.input_feature_ids),
                           str(value.end_condition), value.reversed, value.length.value if value.length else None,
                           list(step.parameter_ids)])
    require(operations == [
        ["sldprt:feature:32", "SteadyStock", "create", ["sldprt:feature:26"], "blind", False, 12.0,
         ["sldprt:parameter:32:D1"]],
        ["sldprt:feature:40", "MovingStock", "create", ["sldprt:feature:33"], "blind", False, 10.0,
         ["sldprt:parameter:40:D1"]],
        ["sldprt:feature:47", "ThroughFeature", "cut", ["sldprt:feature:32", "sldprt:feature:41"],
         "through_all", True, None, []],
    ], "independent operation, depth or selected dependency changed")
    depth_rows = []
    for item in document.parameters:
        owner = item.attributes["typed_archive_owner"]
        depth_rows.append([item.id, item.name, item.owner_id, item.value.value, item.value.unit, str(item.role),
                           owner["dimension_id"], owner["handle_index"], owner["display_index"], owner["slot"]])
    require(depth_rows == [
        ["sldprt:parameter:32:D1", "D1", "sldprt:feature:32", 12.0, "mm", "driving", 27, 273, 271, "f818.f18"],
        ["sldprt:parameter:40:D1", "D1", "sldprt:feature:40", 10.0, "mm", "driving", 34, 345, 344, "f818.f18"],
    ], "the live typed drivers differ")
    scope = typed["cut_body_dependency"]
    require(scope == {"binding": "saved_two_stock_atom_alias", "feature_scope_code": 1, "producer_feature_id": 32,
                      "untouched_producer_feature_id": 40, "consumer_feature_id": 47,
                      "consumed_atom_id": 101, "untouched_atom_id": 102, "result_atom_id": 103},
            "actual selected or surviving owner differs")
    cut = steps[-1]
    require(cut.selection_ids == ("sldprt:feature:47:stock-body",), "portable stock selection is missing")
    choice, = (value for value in document.selections if value.id == cut.selection_ids[0])
    paths = [[p.entity_kind, p.entity_id, p.subelement] for p in choice.path]
    require(paths == [["feature", "sldprt:feature:32", "body"]], "stock selection points away from the consumed producer")
    plane_by_id = {value.id: value for value in document.support_planes}
    support_ids = [value.support_plane_id for value in document.sketches]
    require(support_ids == ["sldprt:plane:2", "sldprt:plane:4", "sldprt:plane:2"]
            and tuple(plane_by_id[value].transform for value in support_ids) == cache.LineageValue.ProfileFrames,
            "portable signed profile frame differs from its exact linked datum")
    profile_rows = []
    for sketch in document.sketches[:2]:
        lines = [value.geometry for value in sketch.entities]
        require(len(lines) == 4 and all(isinstance(line, LineGeometry) for line in lines)
                and len(sketch.constraints) == 4, "actual rectangle or unary relations changed")
        points = {tuple(round(v, 12) for v in (point.x, point.y)) for line in lines for point in (line.start, line.end)}
        profile_rows.append([sketch.id, sorted(points)])
    require(profile_rows == [
        ["sldprt:sketch:26", [(12, -12), (12, -4), (30, -12), (30, -4)]],
        ["sldprt:sketch:33", [(-16, 4), (-16, 12), (-2, 4), (-2, 12)]],
    ], "rectangle extent differs")
    circle = document.sketches[2]
    require(len(circle.entities) == 2 and not circle.constraints, "free profile form changed")
    curve, = (v.geometry for v in circle.entities if isinstance(v.geometry, CircleGeometry))
    point, = (v.geometry for v in circle.entities if isinstance(v.geometry, PointGeometry))
    require(curve.radius == 8 and curve.center.x == 21 and curve.center.y == 0 and point.point == curve.center,
            "free profile circle or its actual centre differs")
    payloads = [[v.id, v.kind, v.source_stream] for v in document.brep_payloads]
    require(payloads == [["sldprt:brep:0", "partition", cache.StreamName], ["sldprt:brep:1", "deltas", cache.StreamName]],
            "the original active or delta payload disappeared")
    body_rows = []
    for body, brep_body in zip(document.bodies, document.brep.bodies, strict=True):
        require(brep_body.design_body_id == body.id and body.attributes["parasolid_payload_ids"] == ("sldprt:brep:0",),
                "solid lost its design or active payload identity")
        topology = body.topology
        body_rows.append([body.id, body.name, body.final_feature_id, brep_body.id, body.attributes["native_kernel_body_index"],
                          [topology.solid_count, topology.shell_count, topology.face_count, topology.edge_count,
                           topology.vertex_count]])
    require(body_rows == [
        ["sldprt:body:atom:102", "MovingStock", "sldprt:feature:40", "sldprt:brep:body:atom:102", 2, [1, 1, 6, 12, 8]],
        ["sldprt:body:atom:103", "ThroughFeature", "sldprt:feature:47", "sldprt:brep:body:atom:103", 6, [1, 1, 8, 18, 12]],
    ], "per-solid identity or topology differs")
    return {"configurations": configurations, "retained_public_rows": rows, "native_root_count": 23,
            "native_member_count": 6, "configuration_helper_count": 1, "operations": operations,
            "native_drivers": depth_rows, "scope": scope, "selection": paths, "profile_supports": support_ids,
            "rectangles_mm": profile_rows, "circle_mm": [curve.center.x, curve.center.y, curve.radius],
            "per_solid_counts": body_rows, "payloads": payloads, "active_geometry_equal": True}


def inject_negative(module, mode, seen):
    original_cache = module.ReadStockCache
    original_project = module.ProjectTyped
    if mode == "cross-depth":
        cache_module = import_module(original_cache.__module__)
        original_link = cache_module.ReadNativeLink

        def crossed_link(*args):
            link = original_link(*args)
            first, second = link.ResolvedValue.RootsValue[-5:-2:2]
            end_first = first.FieldsValue["f818"]
            end_second = second.FieldsValue["f818"]
            require(end_first.FieldsValue["f18"] is not end_second.FieldsValue["f18"], "control depths already alias")
            end_second.FieldsValue["f18"] = end_first.FieldsValue["f18"]
            return link

        cache_module.ReadNativeLink = crossed_link

    def guarded_cache(*args):
        try:
            cache = original_cache(*args)
        except ValueError as error:
            seen.append(str(error))
            raise
        if mode == "detached-producer":
            first, second = cache.LineageValue.StockValues
            detached = replace(first, NodeValue=replace(first.NodeValue))
            return replace(cache, LineageValue=replace(cache.LineageValue, StockValues=(detached, second)))
        return cache

    def guarded_project(model, link, *, StockValue):
        if mode == "cross-datum":
            moving = StockValue.StockValues[1].ProfileValue.FieldsValue["f08"]
            first_support = model.sketches[0].support_plane_id
            model = replace(model, sketches=tuple(
                replace(value, support_plane_id=first_support) if value.object_id == moving else value
                for value in model.sketches
            ))
        try:
            return original_project(model, link, StockValue=StockValue)
        except ValueError as error:
            seen.append(str(error))
            raise

    module.ReadStockCache = guarded_cache
    module.ProjectTyped = guarded_project


def worker(mode):
    sys.path.insert(0, str(REPO / "src"))
    from convert import open_document
    from convert.adapters.base.ReadOptions import ReadOptions
    from convert.adapters.solidworks.Container.Container import SldprtArchive, SldprtFormatError
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadStockCache import ReadStockCache
    from convert.api.ApiContext import KConvertEngine

    for encoding in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        codecs.lookup(encoding)
    for dependency in (
        "interchange.brep.Validation.BrepValidate",
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
        "interchange.geometry.Models.GeometryCurves",
    ):
        import_module(dependency)
    admission = import_module("convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.TryStockPart")
    refusals = []
    if mode in NEGATIVES:
        inject_negative(admission, mode, refusals)
    attempts = []

    def protect(event, _):
        if (event in {"open", "os.listdir", "os.scandir", "os.system", "os.exec", "os.fork", "os.posix_spawn", "os.startfile"}
                or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg."))):
            attempts.append(event)
            raise PermissionError("saved stock document attempted external access: " + event)

    sys.addaudithook(protect)
    payload = sys.stdin.buffer.read()
    expected = UNRESTRICTED if mode == "unrestricted" else SELECTED
    require(sha256(payload).hexdigest() == expected, "worker received unexpected source bytes")
    if mode == "unknown-config":
        try:
            open_document(payload, source_format=FORMAT, configuration="Absent")
        except SldprtFormatError as error:
            require(str(error) == "configuration 'Absent' is unavailable; choices are ['Default']", str(error))
            result = {"refusal": str(error)}
        else:
            raise ValueError("an absent configuration was admitted")
    else:
        if mode == "raw":
            document = KConvertEngine.registry.ReadDocument(
                payload, FormatId=FORMAT, ReadOpts=ReadOptions(extract_raw_brep=True)
            )
        else:
            options = {"configuration": "Default", "include_tessellation": False} if mode == "named" else {}
            if mode == "no-brep":
                options = {"include_brep": False, "include_tessellation": False}
            document = open_document(payload, source_format=FORMAT, **options)
        if mode in ("selected", "named"):
            result = verify_document(document, ReadStockCache(SldprtArchive.from_bytes(payload)))
        else:
            typed = document.metadata["solidworks.typed_resolved_semantics"]
            require(typed["status"] == "unsupported" and typed["diagnostic"] == COMPATIBILITY
                    and len(document.bodies) == 1 and "cut_body_dependency" not in typed
                    and all(not value.id.endswith(":stock-body") for value in document.selections),
                    "alternate record silently used the saved stock path")
            require((document.brep is None) == (mode == "no-brep"), "B-rep option no longer matches compatibility behavior")
            require(tuple(value.kind for value in document.brep_payloads)
                    == (() if mode == "no-brep" else ("partition", "deltas")), "raw payload policy changed")
            if mode in NEGATIVES:
                require(refusals == [NEGATIVES[mode]], "wrong altered owner refusal: " + repr(refusals))
            result = {"compatibility_diagnostic": typed["diagnostic"], "design_body_count": len(document.bodies),
                      "brep_body_count": len(document.brep.bodies) if document.brep else 0,
                      "payload_kinds": [v.kind for v in document.brep_payloads], "altered_owner_refusals": refusals}
    require(not attempts, "worker tried to read external data")
    return {**result, "external_access_attempts": len(attempts)}


def prove(selected, unrestricted):
    head = check_output(("git", "rev-parse", "HEAD"), cwd=REPO, text=True).strip()
    implementation = {path: sha256((REPO / path).read_bytes()).hexdigest() for path in IMPLEMENTATION}
    sources = {}
    for path, name, digest in (
        (selected, "ThroughMultiStock03", SELECTED), (unrestricted, "ThroughAllBodies02", UNRESTRICTED)
    ):
        source = path.resolve(strict=True)
        require(source.parts[-3:] == (name, "DisclosedNative", "ThroughMultiStock.SLDPRT")
                and not path.is_symlink(), "pass only the exact disclosed sources")
        payload = source.read_bytes()
        require(sha256(payload).hexdigest() == digest, "disclosed source hash differs")
        sources[digest] = (source, payload)
    phases = {}
    for mode in MODES:
        digest = UNRESTRICTED if mode == "unrestricted" else SELECTED
        result = run((sys.executable, "-I", "-B", str(HERE), "--worker", mode),
                     input=sources[digest][1], capture_output=True)
        require(result.returncode == 0, result.stderr.decode())
        phases[mode] = json.loads(result.stdout)
    require(phases["selected"] == phases["named"], "equivalent public options produced a different read")
    phases["named"] = {"configuration": "Default", "include_tessellation": False, "matches_selected": True,
                       "external_access_attempts": phases["named"]["external_access_attempts"]}
    require(all(sha256(source.read_bytes()).hexdigest() == digest for digest, (source, _) in sources.items()),
            "a disclosed source changed")
    require(head == check_output(("git", "rev-parse", "HEAD"), cwd=REPO, text=True).strip()
            and all(sha256((REPO / path).read_bytes()).hexdigest() == digest for path, digest in implementation.items()),
            "the reader changed during verification")
    return {"schema": "kit.sw2026.saved-two-stock-document.v1", "baseline_revision": BASE, "worktree_head": head,
            "selected_sha256": SELECTED, "unrestricted_sha256": UNRESTRICTED,
            "tool_sha256": sha256(HERE.read_bytes()).hexdigest(),
            "implementation_sha256": implementation,
            "independent_processes": len(phases), "phases": phases, "native_processes_started": 0,
            "generated_native_files": 0, "heldout_read_count": 0, "public_writer_qualified": False}


def main():
    parser = ArgumentParser()
    parser.add_argument("--selected", type=Path)
    parser.add_argument("--unrestricted", type=Path)
    parser.add_argument("--worker", choices=MODES)
    args = parser.parse_args()
    if args.worker:
        outcome = worker(args.worker)
    else:
        require(args.selected is not None and args.unrestricted is not None, "both disclosed sources are required")
        outcome = prove(args.selected, args.unrestricted)
    print(json.dumps(outcome, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
