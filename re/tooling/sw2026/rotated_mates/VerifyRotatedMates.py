from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from importlib import import_module
from json import dump, dumps, load, loads
from math import isclose
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
BASE = "b0081634f08ca5c3e57ff4fa910e843401a8ca8e"
NATIVE_RECORD = "re/solidworks/measurements/2026/GeneratedRotatedMateNative01.json"
RECEIPT_SHA = "dd062a6526c9fb74aad7e8425fa9c8f585ca9929c27d2ed1836271392ed02aff"
PARENT = "A22CombinedRotated.SLDASM"
CHILD = "CohortChild.SLDPRT"
TRIPLE = ("moMateParallel", "moMateDistanceDim_c", "moMateCoincident")
FORMAT = "solidworks.sldasm"
ORDER = ("ControlBefore", "Generated", "Reopen", "ControlAfter")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finger(value):
    return {"bytes": len(value), "sha256": sha256(value).hexdigest()}


def read_bound(path, expected):
    require(path.is_file() and not path.is_symlink(), f"missing exact disclosed file {path.name}")
    raw = path.read_bytes()
    require(finger(raw)["sha256"] == expected, f"changed exact disclosed file {path.name}")
    return raw


def load_bound(path, expected):
    return loads(read_bound(path, expected))


def paired_inputs(packet, receipt):
    generation, native, source = (receipt[key] for key in ("generation", "native", "source"))
    build = load_bound(packet / "SanitizedGenerationT01.json", generation["guarded_report_sha256"])
    freeze = load_bound(packet / "WriterFrozenT01/FrozenSource.json", generation["source_manifest_sha256"])
    raw = load_bound(packet / "InspectionT01/Result.json", native["result_sha256"])
    trial = load_bound(packet / "PairedTrialT01.json", generation["paired_packet_sha256"])
    lock = load_bound(packet / "GenerationFreezeT01.json", trial["generation_freeze_sha256"])
    request = load_bound(packet / "GeneratedRequestT01.json", generation["request_sha256"])
    source_trial = load_bound(packet / "Trial.json", source["packet_sha256"])
    source_result = load_bound(packet / "Native/SourceEvidence.json", source["native_result_sha256"])
    require(receipt["passed"] and receipt["heldout_inputs_read"] == 0 and raw["passed"]
            and raw["controls_healthy"] and raw["source_bracket_identity"]
            and raw["immutable_inputs_unchanged"] and raw["edit_identity_preserved"]
            and raw["reopen_identity_preserved"] and raw["source_generated_checks"] == native["comparisons"]
            and all(raw["source_generated_checks"].values()) and raw["packet_sha256"] == generation["paired_packet_sha256"]
            and source_result["passed"] and source_result["packet_sha256"] == source["packet_sha256"]
            and source_trial["oracle_sha256"] == receipt["oracle"]["sha256"]
            and freeze["base"] == trial["writer_revision"] == lock["writer_revision"] == generation["writer_revision"]
            and freeze["file_count"] == generation["source_file_count"] == len(freeze["files_sha256"])
            and set(lock) <= set(generation) and all(lock[key] == generation[key] for key in lock)
            and build["input_runtime_file_access_attempts"] == 0 and build["writer_output_count"] == 2
            and set(build["inspection"]["logical_round_trips"]) == {
                "Contents/Config-0", "Contents/Config-0-ResolvedFeatures", "Contents/Config-0-MatesList",
                "Header2", "Contents/Config-0-ModelHeader", "Contents/CMgr", "Contents/Definition",
            }, "native and independently generated provenance disagree")
    inputs = {
        "ControlBefore": {"parent": source["native_parent_sha256"], "child": source["native_child_sha256"]},
        "Generated": {"parent": generation["parent_sha256"], "child": generation["child_sha256"]},
        "Reopen": {"parent": native["saved_parent_sha256"], "child": native["saved_child_sha256"]},
        "ControlAfter": {"parent": source["native_parent_sha256"], "child": source["native_child_sha256"]},
    }
    observations = {phase["role"]: phase for phase in raw["phases"]}
    published = {phase["role"]: phase for phase in native["phases"]}
    require(tuple(observations) == tuple(published) == ORDER, "missing or reordered native control or candidate phase")
    identities, numeric_checks = set(), 0
    for role in ORDER:
        phase, pin = observations[role], published[role]
        record = load_bound(packet / "InspectionT01" / role / "Record.json", pin["record_sha256"])
        result = record["result"]
        identity = result["oracle_identity"]
        require(record["passed"] and result["passed"] and pin["passed"] and phase["passed"]
                and record["job"] == {"role": role, "input": inputs[role]}
                and identity == phase["oracle_identity"] and identity["version_matches"]
                and identity["file_version"] == receipt["oracle"]["version"]
                and identity["sha256"] == trial["oracle_sha256"] == receipt["oracle"]["sha256"]
                and (result["open_errors"], result["open_warnings"]) == (0, 0)
                and not result["dialogs"] and not result["controller_diagnostics"]
                and phase["record_sha256"] == pin["record_sha256"]
                and len(record["checks"]) == phase["numeric_checks"] == pin["numeric_checks"],
                "the measured bundle does not belong to a clean native phase")
        identities.add((identity["process_id"], identity["process_creation_filetime"]))
        numeric_checks += phase["numeric_checks"]
    require(len(identities) == raw["distinct_processes"] == 4
            and numeric_checks == native["numeric_checks"] == 333
            and native["parent_save_status"] == native["child_save_status"] == [True, 0, 0]
            and native["parent_feature_rows"] == 27 and native["child_feature_rows"] == 25,
            "clean native edit save and reopen evidence is incomplete")
    for role, relative in (
        ("ControlBefore", "Native/A22CombinedRotated/author"),
        ("Generated", "FrozenGeneratedT01"), ("Reopen", "WorkingT01"),
    ):
        _ = read_bound(packet / relative / PARENT, inputs[role]["parent"])
        _ = read_bound(packet / relative / CHILD, inputs[role]["child"])
    require(build["assembly"]["sha256"] == inputs["Generated"]["parent"]
            and build["child"]["sha256"] == inputs["Generated"]["child"],
            "the exact full files were not supplied to the generated native phase")
    return request, {name: build[name] for name in ("assembly", "child")}


def bind(root):
    sys.path[:0] = [str(root / "src"), str(root), str(HERE.parent)]
    for name in (
        "interchange.brep.Validation.BrepValidate",
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentComponentValidate",
        "interchange.document.Validation.DocumentGraphValidate",
        "interchange.document.Validation.DocumentMateEntityValidate",
        "interchange.document.Validation.DocumentMateGroupValidate",
        "interchange.document.Validation.DocumentMateValidate",
        "interchange.document.Validation.DocumentMeshValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(name)
    for name in ("utf-8", "utf-8-sig", "utf-16-le", "latin-1", "ascii", "cp1252"):
        lookup(name)


def report_candidate(raw, streams):
    return {**finger(raw), "streams": {name: finger(value) for name, value in sorted(streams.items())}}


def refuse(operation, text):
    try:
        operation()
    except ValueError as error:
        require(text in str(error), f"unexpected refusal: {error}")
        return
    raise ValueError(f"unexpected acceptance before {text}")


def route_refusals(model, native, measured, target):
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.registry.RegistryErrors import NotFoundError
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter

    values = {"native_destination": native["path_name"],
              "solidworks_native_measurement": {"written_at": native["saved_at"], "receipt": measured}}
    writer = SldprtWriter()
    require(not writer.supports(model, target), "the baseline unexpectedly advertises the three-mate target")
    try:
        write_document(model, target, destination_format=FORMAT, values=values, allow_carrier=False)
    except NotFoundError as error:
        require("does not support" in str(error), str(error))
    else:
        raise ValueError("ordinary registry bypassed the unqualified profile")
    refuse(lambda: writer.write(model, target, WriteOptions(values=values)), "matching passing SOLIDWORKS")
    require(not target.parent.exists(), "unqualified destination was touched")
    return ["ordinary_registry_scope", "direct_writer_receipt"]


def bad_graph(parent):
    from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
    from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
    from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    archive = SldprtArchive.from_bytes(parent)
    link = ReadNativeLink(archive, 0, AssemblyValue=True)
    stream = "Contents/Config-0-MatesList"
    mates = ReadMatesMut(archive.require(stream), link.ResolvedValue)
    mates.RootsValue[0].FieldsValue["f388"] = 1
    encoded, _ = WriteMatesMut(mates.RootsValue, link.ResolvedValue)
    return BuildSldprt(archive.streams | {stream: encoded}, FormatVersion=4)


def linked_read(root_path, payloads, bundle):
    from convert.adapters.solidworks.Core.AssemblyWriting.Readback.ReadBundle import ReadBundle
    from convert.adapters.solidworks.Container.Archive import ContainerMo

    classifier = import_module("convert.adapters.solidworks.Core.TypedMates.CanReadMates")
    adapter = import_module("convert.adapters.solidworks.Core.TypedMates.WithTypedMates")
    baseline = classifier.HasPlanarMates

    def recognize(env):
        if baseline(env):
            return True
        native = env.NativeValue
        if (env.ArchiveValue.format_version != 4 or ContainerMo(env.ArchiveValue.streams) != 19000
                or len(native.configurations) != 1 or len(native.mate_lists) != 1):
            return False
        config, mates = native.configurations[0], native.mate_lists[0]
        return (config.configuration_id == 0 and config.model_id == native.root_definition_id == mates.owner_definition_id
                and mates.stream == "Contents/Config-0-MatesList"
                and mates.declared_count == len(mates.mates)
                and tuple(mate.class_name for mate in mates.mates) == TRIPLE)

    refuse(lambda: ReadBundle(payloads, root_path), "has no entities")
    with patch.object(classifier, "HasPlanarMates", recognize), patch.object(adapter, "HasPlanarMates", recognize):
        doc = ReadBundle(payloads, root_path)
        malformed = payloads | {root_path: bad_graph(payloads[root_path])}
        refuse(lambda: ReadBundle(malformed, root_path), "typed mate has unsupported auxiliary options")
    graph = doc.assembly
    require(graph is not None and len(graph.mate_groups) == 1 and len(graph.mates) == 3
            and len(graph.mate_entities) == 6 and len(graph.instances) == 2
            and tuple(item.fixed for item in graph.instances) == (True, False),
            "three-mate linked read did not retain complete group ownership")
    by_id = {entity.id: entity for entity in graph.mate_entities}
    child = graph.documents[0].document
    datum = {item.id: item.name for item in child.support_planes}
    for order, (mate, row) in enumerate(zip(graph.mates, bundle["mates"], strict=True)):
        require((mate.order, str(mate.kind), mate.name) == (order, row["kind"], row["name"]),
                "native mate kind or order changed")
        for entity_id, selector in zip(mate.entity_ids, row["endpoints"], strict=True):
            entity = by_id[entity_id]
            require(entity.instance_path == (graph.instances[selector["occurrence"]].id,)
                    and datum[entity.source_entity_id] == selector["datum"],
                    "native mate endpoint does not resolve to the actual child datum")
    for occurrence, authored in zip(graph.instances, bundle["occurrences"], strict=True):
        matrix = occurrence.attributes["typed_placement_m"]
        placement = authored["placement"]
        require(all(isclose(a, b, rel_tol=0.0, abs_tol=2e-16)
                    for a, b in zip((*matrix[:3], *matrix[4:7], *matrix[12:15]),
                                    (*placement["u"], *placement["v"], *placement["origin"]), strict=True)),
                "typed placement differs from the independently authored rotation and translation")
    depth = graph.mates[1]
    driver = doc.parameter(depth.parameter_ids[0])
    require(driver.owner_id == depth.id and depth.value == driver.value
            and driver.value.value == 1000 * bundle["mates"][1]["distance_m"]
            and tuple(value.value.value for value in child.parameters) == (40.0, 20.0, 10.0),
            "actual driving dimension or child drivers were lost")
    report = doc.metadata["solidworks.typed_mates_semantics"]
    require(report["status"] == "admitted" and report["full_selected_mate_graph"] is True,
            "probe returned an unqualified legacy projection")
    return {"mate_order": [str(row.kind) for row in graph.mates], "owned_endpoint_count": 6,
            "distance_mm": driver.value.value, "driver_native_id": driver.provenance.native_id,
            "map_base": report["map_base"], "map_terminal": report["map_terminal"],
            "child_dimensions_mm": [value.value.value for value in child.parameters],
            "baseline_reader_refusal": "has no entities",
            "typed_reader_rejected_unqualified_parallel_options": True}


def guard_build(root, data):
    bind(root)
    request = data["request"]
    from BuildHistoricalRotated import build
    from ProjectRotatedModel import author_model, literal_recipes
    from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.MakePlanarGroup import MakePlanarGroup
    from convert.adapters.solidworks.Archive.Construction.Part.MakeRectDimPart import MakeRectDimPart
    from convert.adapters.solidworks.Core.AssemblyPreparation.PlanAsmWrite import PlanAsmWrite
    from convert.adapters.solidworks.Core.AssemblyPreparation.PrepareAssembly import PrepareAssembly

    bundle = request["bundle"]
    require(request["include_xml_metadata"] is True, "this historical bundle needs both indexes")
    disclosed = bundle["assembly"]["output"]
    attempted = []
    enabled = False

    def deny(event, values):
        if enabled and (event in ("open", "os.scandir", "os.listdir", "os.system", "os.startfile",
                                  "subprocess.Popen", "ctypes.dlopen", "ctypes.dlsym")
                        or event.startswith(("socket.", "os.exec", "os.spawn", "os.posix_spawn"))):
            attempted.append(event)
            raise PermissionError(f"unexpected construction data access: {event} {values[0] if values else ''}")

    sys.addaudithook(deny)
    with TemporaryDirectory(prefix="KitRotatedGuard-") as temporary:
        target = Path(temporary) / "unpublished" / PARENT
        enabled = True
        try:
            model = author_model(bundle)
            plan = PlanAsmWrite(model, disclosed["path_name"], disclosed["saved_at"])
            ordinary = PrepareAssembly(model, disclosed["path_name"], disclosed["saved_at"])
            parent, leaf, dimensions = literal_recipes(bundle, plan)
            explicit_child = MakeRectDimPart(plan.ChildDocument, leaf, dimensions)
            explicit_parent = MakePlanarGroup(explicit_child, parent, plan.Occurrences,
                                              plan.MatesValue, plan.FixedIndex)
            exact = build(bundle, plan)
            refusals = route_refusals(model, disclosed, data["receipt"], target)
        finally:
            enabled = False
    require(not attempted and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules),
            "candidate construction used an input file or CAD runtime")
    relative = Path("/KitMeasuredRotated") / PARENT
    typed = linked_read(relative, {relative: exact[0][0], relative.with_name(CHILD): exact[1][0]}, bundle)
    return {
        "input_reads": len(attempted),
        "report": typed,
        "publication_refusals": refusals,
        "historical": {key: report_candidate(*value) for key, value in zip(("assembly", "child"), exact, strict=True)},
        "ordinary": {key: report_candidate(value.BytesValue, value.StreamsValue) for key, value in
                     (("assembly", ordinary), ("child", ordinary.ChildValue))},
        "explicit": {key: report_candidate(value.BytesValue, value.StreamsValue) for key, value in
                     (("assembly", explicit_parent), ("child", explicit_child))},
    }


def warm_frontier(root, packet, receipt):
    bind(root)
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedMates.ReadMateChild import ReadMateChild
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    observations = {}
    for role, relative, digest in (
        ("native_original_parent", "Native/A22CombinedRotated/author", receipt["source"]["native_parent_sha256"]),
        ("native_edited_parent", "WorkingT01", receipt["native"]["saved_parent_sha256"]),
    ):
        data = read_bound(packet / relative / PARENT, digest)
        archive = SldprtArchive.from_bytes(data)
        message = "unsupported SOLIDWORKS body class moAssemblyTimings_c schema 1"
        refuse(lambda: ReadNativeLink(archive, 0, AssemblyValue=True), message)
        observations[role] = message
    digest = receipt["native"]["saved_child_sha256"]
    data = read_bound(packet / "WorkingT01" / CHILD, digest)
    message = "unsupported SOLIDWORKS body class moLinkedAtomIdNode_c schema 1"
    refuse(lambda: ReadMateChild(data, digest), message)
    observations["native_edited_child"] = message
    return observations


def supervise(root, packet, output):
    receipt = load_bound(root / NATIVE_RECORD, RECEIPT_SHA)
    request, historical = paired_inputs(packet, receipt)
    results = []
    for _ in range(2):
        worker = run([sys.executable, "-I", "-B", str(HERE), "--root", str(root), "--worker"],
                     input=dumps({"request": request, "receipt": receipt}, allow_nan=False),
                     capture_output=True, text=True, timeout=90)
        require(worker.returncode == 0 and not worker.stderr, worker.stderr)
        results.append(loads(worker.stdout))
    require(results[0] == results[1] and results[0]["historical"] == historical,
            "fresh candidates did not independently reproduce the complete measured bundle")
    result = results[0]
    changed = {}
    for name, expected in historical.items():
        current = result["explicit"][name]["streams"]
        changed[name] = [stream for stream in sorted(current.keys() | expected["streams"].keys())
                         if current.get(stream) != expected["streams"].get(stream)]
    require(result["ordinary"] != historical and changed == {
        "assembly": ["Contents/CMgrHdr2", "Contents/Config-0-MatesList", "Contents/Config-0-ModelHeader", "Header2"],
        "child": ["Contents/Config-0", "Contents/Config-0-ResolvedFeatures", "swXmlContents/KeyWords"],
    }, "the ordinary or explicit recipe difference boundary changed")
    script_hashes = {path.name: finger(path.read_bytes())["sha256"] for path in sorted(HERE.parent.glob("*.py"))}
    evidence = {"schema": "kit.sw2026.rotated-mates-main-boundary.v1", "production_base": BASE,
                "source_native_receipt_sha256": RECEIPT_SHA, "guarded_processes": len(results),
                "native_processes_started": 0, "preexisting_native_lifetimes": 4,
                "preexisting_native_numeric_checks": 333, "heldout_inputs_read": 0,
                "public_writer_qualified": False, "scripts_sha256": script_hashes,
                "warm_reader_first_refusals": warm_frontier(root, packet, receipt),
                "typed_recipe_remaining_stream_differences": changed, **result}
    with output.open("x", encoding="utf-8") as stream:
        dump(evidence, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(finger(output.read_bytes())["sha256"])


if __name__ == "__main__":
    cli = ArgumentParser()
    cli.add_argument("--root", type=Path, default=ROOT)
    cli.add_argument("--disclosed", type=Path)
    cli.add_argument("--output", type=Path)
    cli.add_argument("--worker", action="store_true")
    args = cli.parse_args()
    if args.worker:
        print(dumps(guard_build(args.root, load(sys.stdin)), sort_keys=True, allow_nan=False))
    else:
        supervise(args.root, args.disclosed, args.output)
