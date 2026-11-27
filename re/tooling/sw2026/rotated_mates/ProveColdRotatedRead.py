from argparse import ArgumentParser
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
from json import dump, dumps, load, loads
from math import isclose
from os import O_CREAT, O_RDWR, O_TRUNC, O_WRONLY, fsdecode
from pathlib import Path
from subprocess import check_output, run
from tempfile import TemporaryDirectory
import sys


HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))
from VerifyRotatedMates import (
    CHILD, FORMAT, NATIVE_RECORD, PARENT, RECEIPT_SHA, bad_graph, bind, finger,
    load_bound, paired_inputs, read_bound, refuse, require, route_refusals,
)


ROOT = HERE.parents[4]
BASE = "77d8cef5df85299070379a73595b764cb7c77049"
SCOPE = "cold_parallel_distance_coincident"
COLD_PATH = "FrozenGeneratedT01"


@contextmanager
def source_only(paths, rules=()):
    expected = {path.resolve() for path in paths}
    schemas = {path.resolve() for path in rules}
    directories = {path.parent for path in expected}
    accessed = Counter()
    enabled = True

    def audit(event, values):
        if not enabled:
            return
        if (event in ("subprocess.Popen", "os.startfile", "os.system", "os.fork", "ctypes.dlopen", "ctypes.dlsym")
                or event.startswith(("os.exec", "os.spawn", "os.posix_spawn", "socket."))):
            raise PermissionError(f"unexpected reader runtime: {event}")
        if event not in ("open", "os.listdir", "os.scandir"):
            return
        location = values[0] if values else None
        path = Path(fsdecode(location)).resolve() if isinstance(location, (str, bytes)) else None
        caller = sys._getframe(1)
        import_code = caller.f_code.co_filename == "<frozen importlib._bootstrap_external>"
        if event == "open":
            if import_code and caller.f_code.co_name == "get_data" and path is not None and path.suffix in (".py", ".pyc"):
                return
            if values[2] & (O_WRONLY | O_RDWR | O_CREAT | O_TRUNC):
                raise PermissionError(f"unexpected write access during inspection: {path}")
            if path in expected or path in schemas:
                accessed[path.name] += 1
                return
            raise PermissionError(f"unexpected reader file access: {path}")
        if event in ("os.listdir", "os.scandir"):
            if import_code or path in directories:
                return
            raise PermissionError(f"unexpected reader directory access: {path}")


    sys.addaudithook(audit)
    try:
        yield accessed
    finally:
        enabled = False


def inspect_group(document, receipt, bundle, *, include_brep):
    from convert.adapters.solidworks.Core.AssemblyPreparation.Readback.IsPlanarRead import IsPlanarRead

    graph = document.assembly
    status = document.metadata["solidworks.typed_mates_semantics"]
    child = graph.documents[0].document
    require(document.source.sha256 == receipt["generation"]["parent_sha256"]
            and child.source.sha256 == receipt["generation"]["child_sha256"],
            "the public read did not use the measured parent and actual child")
    require(status["status"] == "admitted" and status["scope"] == SCOPE
            and status["full_selected_mate_graph"] is True
            and status["public_writer_qualified"] is False and not IsPlanarRead(document),
            "cold inspection reached a public writer qualification")
    require(len(graph.mates) == 3 and len(graph.mate_groups) == 1
            and graph.mate_groups[0].mate_ids == tuple(mate.id for mate in graph.mates)
            and len(graph.mate_entities) == 6 and len(graph.instances) == 2
            and tuple(item.fixed for item in graph.instances) == (True, False),
            "the three physical mates lost their shared ownership")
    datums = {datum.id: datum.name for datum in child.support_planes}
    picks = {item.id: item for item in graph.mate_entities}
    for order, (mate, authored) in enumerate(zip(graph.mates, bundle["mates"], strict=True)):
        require((mate.order, str(mate.kind), mate.name) == (order, authored["kind"], authored["name"]),
                "public read changed a native name, order or class")
        for selection, endpoint in zip(mate.entity_ids, authored["endpoints"], strict=True):
            resolved = picks[selection]
            require(resolved.instance_path == (graph.instances[endpoint["occurrence"]].id,)
                    and datums[resolved.source_entity_id] == endpoint["datum"],
                    "a public endpoint lost its actual instance and datum")
    for occurrence, authored in zip(graph.instances, bundle["occurrences"], strict=True):
        matrix = occurrence.attributes["typed_placement_m"]
        place = authored["placement"]
        require(all(isclose(a, b, rel_tol=0.0, abs_tol=2e-16) for a, b in zip(
            (*matrix[:3], *matrix[4:7], *matrix[12:15]), (*place["u"], *place["v"], *place["origin"]), strict=True,
        )), "public placement differs from the authored occurrence frame")
    (driver,) = document.parameters
    distance = graph.mates[1]
    require(driver.name == "D1" and driver.role.value == "driving"
            and driver.value.value == 63.5 and driver.value == distance.value
            and driver.owner_id == distance.id and distance.parameter_ids == (driver.id,)
            and driver.provenance.native_id == "20",
            "public distance does not use the live typed parameter")
    require([row.value.value for row in child.parameters] == [40.0, 20.0, 10.0]
            and (child.brep is not None) == include_brep, "the child scope depends on geometry mode")
    if include_brep:
        (body,) = child.bodies
        topology = body.topology
        require((topology.solid_count, topology.face_count, topology.edge_count, topology.vertex_count)
                == (1, 6, 12, 8) and topology.volume == 8000.0,
                "geometry read did not retain the rectangular child solid")
    return driver


def read_cold(root, packet, receipt, request):
    from convert import open_document
    from convert.adapters.base.ReadOptions import ReadOptions
    from convert.api.ApiContext import KConvertEngine

    parent = packet / COLD_PATH / PARENT
    child = parent.with_name(CHILD)
    directory_evidence = {}
    schema = root / "src/convert/adapters/solidworks/Config/RootLayout.json"
    from convert.adapters.solidworks.Core.AssemblyWriting.Readback.ReadBundle import ReadBundle

    raw = read_bound(parent, receipt["generation"]["parent_sha256"])
    part = read_bound(child, receipt["generation"]["child_sha256"])
    with source_only(()) as memory_access:
        in_memory = ReadBundle({parent: raw, child: part}, parent)
    inspect_group(in_memory, receipt, request["bundle"], include_brep=True)
    require(not memory_access, "the linked in-memory read used a data file")
    with source_only((parent, child), (schema,)) as full_access:
        full = open_document(parent, source_format=FORMAT, strict=True)
    with source_only((parent, child), (schema,)) as design_access:
        design = open_document(parent, source_format=FORMAT, strict=True, include_brep=False)
    for mode, doc, accesses in (("full", full, full_access), ("design", design, design_access)):
        driver = inspect_group(doc, receipt, request["bundle"], include_brep=mode == "full")
        require({PARENT, CHILD} <= set(accesses) <= {PARENT, CHILD, schema.name},
                "the codec did not open both actual linked files")
        directory_evidence[mode] = {
            "source_opens": {name: accesses[name] for name in (PARENT, CHILD)},
            "packaged_schema_opens": accesses[schema.name],
            "mate_driver_mm": driver.value.value, "mate_driver_id": driver.id, "child_brep": mode == "full",
        }
    require(full.assembly.mates == design.assembly.mates and full.parameters == design.parameters
            and full.assembly.mate_entities == design.assembly.mate_entities
            and full.assembly.instances == design.assembly.instances, "geometry mode changed the native design graph")
    values = {"resolve_components": False, "discover_companions": False}
    with source_only((parent,)) as deferred_access:
        deferred = KConvertEngine.read(parent, format_id=FORMAT, options=ReadOptions(strict=True, values=values))
    graph = deferred.assembly
    require(deferred.metadata["solidworks.typed_mates_semantics"]["status"] == "deferred"
            and not graph.documents and not graph.mates and not graph.mate_entities
            and not deferred.parameters and len(graph.instances) == 2
            and any(payload.format_id == "solidworks.mates" for payload in deferred.brep_payloads),
            "the deferred mode consumed a linked child or exposed an incomplete group")
    with TemporaryDirectory(prefix="KitRotatedReadback-") as temporary:
        target = Path(temporary) / "unpublished" / PARENT
        write_refusals = route_refusals(full, request["bundle"]["assembly"]["output"], receipt, target)
    return {"scope": SCOPE, "modes": directory_evidence, "deferred_source_opens": dict(deferred_access),
            "writer_refusals": write_refusals, "public_writer_qualified": False,
            "guarded_in_memory_data_reads": sum(memory_access.values()),
            "packaged_schema_sha256": finger(schema.read_bytes())["sha256"]}


def malformed_reads(packet, receipt, request):
    from BuildHistoricalRotated import build
    from ProjectRotatedModel import author_model
    from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
    from convert.adapters.solidworks.Core.AssemblyPreparation.PlanAsmWrite import PlanAsmWrite
    from convert.adapters.solidworks.Core.AssemblyWriting.Readback.ReadBundle import ReadBundle

    original = packet / COLD_PATH / PARENT
    raw = read_bound(original, receipt["generation"]["parent_sha256"])
    child = read_bound(original.with_name(CHILD), receipt["generation"]["child_sha256"])
    virtual = Path("/KitRotatedReadContrast") / PARENT
    values = {virtual: raw, virtual.with_name(CHILD): child}
    refuse(lambda: ReadBundle(values | {virtual: bad_graph(raw)}, virtual), "unsupported auxiliary options")

    unrelated = deepcopy(request["bundle"])
    first = unrelated["mates"][0]
    first["kind"] = "coincident"
    for value in first["endpoints"]:
        value["datum"] = "Right Plane"
    intent = unrelated["assembly"]["output"]
    plan = PlanAsmWrite(author_model(unrelated), intent["path_name"], intent["saved_at"])
    alternate, alternate_child = build(unrelated, plan)
    require(alternate_child[0] == child, "the stray mate class contrast changed the shared part")
    refuse(lambda: ReadBundle(values | {virtual: alternate[0]}, virtual), "has no entities")

    archive = SldprtArchive.from_bytes(child)
    scoped = BuildSldprt(archive.streams | {"docProps/ArchiveContrast": b"x"}, FormatVersion=4)
    refuse(lambda: ReadBundle(values | {virtual.with_name(CHILD): scoped}, virtual),
           "requires an ordinary cold child archive")
    return ["unknown_parallel_option", "stray_mate_class", "unqualified_cold_child_stream"]


def warm_snapshots(packet, receipt):
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedMates.ReadMateChild import ReadMateChild
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    results = {}
    for label, relative, parent_hash, child_hash in (
        ("original", "Native/A22CombinedRotated/author", receipt["source"]["native_parent_sha256"],
         receipt["source"]["native_child_sha256"]),
        ("saved_edit", "WorkingT01", receipt["native"]["saved_parent_sha256"], receipt["native"]["saved_child_sha256"]),
    ):
        path = packet / relative / PARENT
        parent = read_bound(path, parent_hash)
        child = path.with_name(CHILD)
        _ = read_bound(child, child_hash)
        snapshots = {}
        for mode, geometry in (("full", True), ("design", False)):
            document = open_document(path, source_format=FORMAT, strict=True, include_brep=geometry)
            require(not document.parameters and "solidworks.typed_mates_semantics" not in document.metadata
                    and len(document.assembly.mates) == 3, "warm read entered cold typed admission")
            snapshots[mode] = finger(document.to_json(indent=None).encode())["sha256"]
        linked = SldprtArchive.from_bytes(parent)
        stop = "unsupported SOLIDWORKS body class moAssemblyTimings_c schema 1"
        refuse(lambda: ReadNativeLink(linked, 0, AssemblyValue=True), stop)
        results[label] = {"legacy_snapshot_sha256": snapshots, "typed_first_refusal": stop}
    saved_hash = receipt["native"]["saved_child_sha256"]
    saved_child = read_bound(packet / "WorkingT01" / CHILD, saved_hash)
    stop = "unsupported SOLIDWORKS body class moLinkedAtomIdNode_c schema 1"
    refuse(lambda: ReadMateChild(saved_child, saved_hash), stop)
    results["saved_child_typed_first_refusal"] = stop
    return results


def run_worker(root, request, baseline):
    bind(root)
    packet = Path(request["disclosed"])
    receipt = request["receipt"]
    if baseline:
        return {"warm": warm_snapshots(packet, receipt)}
    cold = read_cold(root, packet, receipt, request["authored"])
    return {"warm": warm_snapshots(packet, receipt), "cold": cold,
            "malformed": malformed_reads(packet, receipt, request["authored"])}


def supervise(packet, output):
    receipt = load_bound(ROOT / NATIVE_RECORD, RECEIPT_SHA)
    authored, _ = paired_inputs(packet, receipt)
    args = {"disclosed": str(packet.resolve()), "receipt": receipt, "authored": authored}

    def worker(root, baseline=False):
        command = [sys.executable, "-I", "-B", str(HERE), "--worker", "--code-root", str(root)]
        if baseline:
            command.append("--baseline")
        child = run(command, input=dumps(args), encoding="utf-8", capture_output=True,
                    timeout=90, check=False)
        require(child.returncode == 0 and not child.stderr, child.stderr)
        return loads(child.stdout)

    with TemporaryDirectory(prefix="KitRotatedReaderBaseline-") as directory:
        prior = Path(directory)
        archive = check_output(["git", "archive", BASE, "src"], cwd=ROOT)
        extract = run(["tar", "-x", "-C", directory], input=archive, capture_output=True, check=False, timeout=60)
        require(extract.returncode == 0 and not extract.stderr, "could not stage the exact prior reader source")
        original = worker(prior, baseline=True)
    first, second = worker(ROOT), worker(ROOT)
    require(first == second and first["warm"] == original["warm"],
            "guarded cold reads were unstable or changed prior warm inspection")
    tracked = set()
    for query in (["diff", "--name-only", "-z", BASE, "--", "src"],
                  ["ls-files", "--others", "--exclude-standard", "-z", "--", "src"]):
        tracked.update(check_output(["git", *query], cwd=ROOT).decode().split("\0"))
    evidence = {**first, "schema": "kit.sw2026.cold-rotated-strict-read.v1",
                "native_receipt_sha256": RECEIPT_SHA, "prior_reader": BASE,
                "guarded_current_workers": 2, "baseline_warm_worker": 1, "native_processes_started": 0,
                "method_sha256": finger(HERE.read_bytes())["sha256"],
                "source_sha256": {name: finger((ROOT / name).read_bytes())["sha256"] for name in sorted(tracked - {""})}}
    with output.open("x", encoding="utf-8") as stream:
        dump(evidence, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(finger(output.read_bytes())["sha256"])


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--disclosed", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--code-root", type=Path, default=ROOT)
    options = parser.parse_args()
    if options.worker:
        print(dumps(run_worker(options.code_root, load(sys.stdin), options.baseline), sort_keys=True))
    else:
        supervise(options.disclosed, options.output)
