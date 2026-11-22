from argparse import ArgumentParser
from base64 import b64decode, b64encode
from codecs import lookup
from collections import Counter
from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
from math import isclose, isfinite
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
import sys
from tarfile import open as open_tar
from tempfile import TemporaryDirectory


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TOOL_ROOT = "re/tooling/sw2026"
RESEARCH = TOOL_ROOT + "/imported_body_source/"
BASE = "8f02732268651f8d3123ab727c80ce813285323c"
SDK_TREE = "392993e1c5f530d854c132482b268d1554d8c5c7"
TOLERANCE_RECEIPT = "cd24aac3a2f5bf2970cf00bffda194b4738f2536a8cd5fda760ff1a623f50b18"
OWNER_RECEIPT = "76471602145cacdac72876f471b00d74cf41397df85ed946e5a719d62afaeb1e"
MEASURES = "re/solidworks/measurements/2026/"
SOURCE_TOOLS = ("BuildBakedLabelPair.py", "AuditBakedFcstdSources.py", "ProveBakedLocalTolerance.py")
BUILDER = Path(__file__).name
EPOCH = 1795300000

sys.path.insert(0, str(HERE))
from ObserveBakedTolerancePart import (
    BUILD, CASES, CONTROL, GUEST, JOB_SCHEMA, OBSERVER, ORACLE, PHASES, TOOLS,
    artifact, checked, encode, require, verify,
)


@contextmanager
def model_only():
    active, accesses = True, []

    def audit(event, _args):
        if active and (event in {"open", "os.scandir", "os.listdir", "os.system", "os.exec",
                                "os.fork", "os.forkpty", "os.posix_spawn", "subprocess.Popen", "ctypes.dlopen"}
                       or event.startswith("socket.")):
            accesses.append(event)
            raise PermissionError("model-only construction attempted " + event)

    sys.addaudithook(audit)
    try:
        yield accesses
    finally:
        active = False


def git(*args):
    return check_output(("git", "-C", str(ROOT), *args))


def project(directory):
    from AuditBakedFcstdSources import LOCK, physical_owner
    from ProveBakedLocalTolerance import import_scope, ring_signature

    sys.path.insert(0, str(ROOT / "src"))
    from convert import open_document
    from convert.adapters.solidworks.Core.Partition.PartMassRings import ReadMassRings

    owner_data = checked(ROOT / (MEASURES + "DisclosedBakedFcstdOwners01.json"), OWNER_RECEIPT)
    source = json.loads(owner_data)
    previous = json.loads(checked(ROOT / (MEASURES + "DisclosedBakedLocalTolerance01.json"), TOLERANCE_RECEIPT))
    lock_data = checked(directory / "DisclosedSourceLock01.json", LOCK)
    lock = json.loads(lock_data)
    require(source["source_lock_sha256"] == LOCK and lock["passed"] and lock["writer_outputs"] == 0
            and previous["source_owner_audit_sha256"] == OWNER_RECEIPT
            and previous["tool_sha256"] == sha256((HERE / SOURCE_TOOLS[2]).read_bytes()).hexdigest(),
            "disclosed source lock or preceding typed transmit proof differs")
    cases = {}
    for name, locked in zip((*CASES, "ParametricControl"), lock["inputs"], strict=True):
        filename = name + ".FCStd"
        evidence = source["cases"][filename]
        require(locked == evidence["source_lock"], "physical Shape evidence escaped its source lock")
        path = directory / filename
        physical = physical_owner(path, locked)
        require(json.loads(json.dumps(physical)) == evidence["physical_owners"],
                "source physical ownership differs from its independent audit")
        raw = checked(path, locked["file_sha256"])
        document = open_document(BytesIO(raw), source_format="freecad.fcstd", strict=True)
        if name == "ParametricControl":
            require(physical["class"] == "Part::Box" and set(physical["driver_lengths_mm"]) == {"Length", "Width", "Height"},
                    "negative is no longer the real editable primitive")
            try:
                import_scope(document, locked)
            except ValueError as exc:
                require(str(exc) == "source is not an independently baked feature", "primitive refused at the wrong owner")
            else:
                raise ValueError("live parametrically owned box entered the baked projection")
            negative = artifact(raw)
            continue
        selected, configuration = import_scope(document, locked)
        values = {tuple(row) for row in selected["tolerances_mm"].values()}
        require(len(values) == 1 and len(next(iter(values))) == 1, "expected one authored source tolerance at every boundary owner")
        tolerance, = next(iter(values))
        require(isfinite(tolerance) and tolerance > 0, "source tolerance must be finite and positive")
        cases[name] = {
            "source": artifact(raw), "shape_sha256": locked["shape_sha256"], "feature": physical["label"],
            "configuration": configuration, "bounds_mm": selected["bounds_mm"], "tolerance_mm": tolerance,
            "outward_rings": ring_signature(ReadMassRings(document.brep)),
        }
    require(set(cases) == set(CASES), "disclosed baked pair is incomplete")
    return cases, negative, previous["sources"]


def inspect_part(blob, case, name, *, warm):
    from convert import open_document
    from convert.Geometry.Parasolid import BuildPartModel, KMissingParam
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeader
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Container.Format import KLocalBodyStream, KPartitionStream
    from convert.adapters.solidworks.Core.Partition.PartMassRings import ReadMassRings
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Local.ReadLocalOwner import ReadLocalOwner
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.CheckLocalBodyGraph import CheckLocalGraph
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.MakeLocalBodyTables import MakeLocalTables
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalBodyNodes import ReadLocalNodes
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalEnvelope import ReadLocalWrap
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalPayload import ReadLocalState
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from ProveBakedLocalTolerance import KIND_OWNERS, ring_signature

    archive = SldprtArchive.from_bytes(blob)
    local = archive.get(KLocalBodyStream)
    if warm and local is None:
        return {"status": "local_group_absent", "part": artifact(blob), "active_partition_present": KPartitionStream in archive.streams}
    document = open_document(blob, source_format="solidworks.sldprt", strict=True)
    document.assert_valid()
    (body,) = document.bodies
    config, = document.configurations
    require(config.active and config.name == case["configuration"] and document.brep is not None
            and document.brep.bodies[0].design_body_id == body.id,
            "strict native read did not bind the actual active configuration and solid")
    payload, mark, predecessor = ReadLocalState(document.brep_payloads, archive.require(KPartitionStream))
    group = ReadLocalWrap(archive.require(KLocalBodyStream), payload)
    atom, feature = ReadLocalOwner(ReadNativeLink(archive, 0), group, mark)
    require(group == case["feature"] == body.name and body.final_feature_id == f"sldprt:feature:{feature}",
            "local group is detached from the actual final import")
    nodes, offsets = ReadLocalNodes(payload)
    CheckLocalGraph(nodes, AllowStoredAttrs=warm)
    decoded = BuildPartModel(MakeLocalTables(nodes, offsets))
    require(not decoded.validate() and (len(decoded.bodies), len(decoded.faces), len(decoded.edges), len(decoded.vertices)) == (1, 6, 12, 8),
            "typed local nodes do not reconstruct the complete box")
    rings = ring_signature(ReadMassRings(decoded))
    require(all(isclose(a, b, rel_tol=0, abs_tol=1e-9)
                for left, right in zip(rings, case["outward_rings"], strict=True)
                for p, q in zip(left, right, strict=True)
                for a, b in zip(p, q, strict=True)),
            "local node collection differs from the oriented source rings")
    values = {label: Counter(node.FieldsValue["tolerance"] for node in nodes.values() if node.KindValue == kind)
              for kind, label in KIND_OWNERS.items()}
    require({label: sum(counts.values()) for label, counts in values.items()} == {"faces": 6, "edges": 12, "vertices": 8},
            "local tolerance inventory lacks a topology owner")
    tolerance = case["tolerance_m"]
    all_values = tuple(value for counts in values.values() for value in counts)
    if all(value == tolerance for value in all_values):
        status = "exact"
    elif all(isclose(value, tolerance, rel_tol=1e-6, abs_tol=0) for value in all_values):
        status = "within_six_significant_figures"
    elif all(value == KMissingParam for value in all_values):
        status = "native_missing_sentinel"
    else:
        status = "changed"
    locator = str(PureWindowsPath(GUEST) / ("Saved" if warm else "Candidates") / (name + ".SLDPRT"))
    header_locators = [ReadHeader(archive.require(key), 19000).SelfFile.PathValue
                       for key in ("Header2", "Contents/Config-0-ModelHeader")]
    if not warm:
        require(header_locators == [locator, locator] and status == "exact", "generated self identity or tolerance differs")
    return {"status": status, "part": artifact(blob), "kernel": artifact(payload), "local_stream": artifact(local),
            "header_self_path_matches": [PureWindowsPath(path) == PureWindowsPath(locator) for path in header_locators],
            "feature_id": feature, "atom_id": atom.FieldsValue["f140"], "mark": mark, "predecessor": predecessor,
            "local_node_count": len(nodes), "oriented_faces": len(rings),
            "tolerance_values_m": {label: {value.hex(): count for value, count in sorted(counts.items())}
                                   for label, counts in values.items()}}


def construct(sdk, requests):
    sys.path.insert(0, str(sdk))
    from BuildBakedLabelPair import computed_box
    from ProveBakedLocalTolerance import KIND_OWNERS, ring_signature
    from convert.Geometry.Parasolid import KMissingParam
    from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
    from convert.adapters.solidworks.Archive.Construction.Part.Imports.MakeBareImport import MakeBareImport
    from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeLocalPrism import MakeLocalPrism
    from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import KMillimetersPerMeter
    from convert.adapters.solidworks.Archive.Partition.LocalWrite.EncodeLocalBody import EncodeLocalBody
    from convert.adapters.solidworks.Archive.Partition.LocalWrite.EncodeLocalXmt import EncodeLocalXmt
    from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
    from convert.adapters.solidworks.Container.Format import KLocalBodyStream
    from convert.adapters.solidworks.Core.Partition.PartMassRings import ReadMassRings
    from convert.adapters.solidworks.Core.Preparation.Imports.ImportPartPlan import ImportPartPlan
    from convert.adapters.solidworks.Core.Preparation.Imports.MakeImportLight import MakeImportLight
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalBodyNodes import ReadLocalNodes

    for codec in ("ascii", "latin-1", "utf-8", "utf-16-le"):
        lookup(codec)
    output = {}
    for name, case in requests.items():
        locator = str(PureWindowsPath(GUEST) / "Candidates" / (name + ".SLDPRT"))
        with model_only() as accesses:
            neutral = computed_box(case["bounds_mm"], case["configuration"])
            require(json.loads(json.dumps(ring_signature(ReadMassRings(neutral.brep)))) == case["outward_rings"],
                    "fresh model differs from actual signed source geometry")
            plan = ImportPartPlan(name, case["configuration"], case["feature"])
            recipe = replace(MakePartRecipe(plan, EPOCH), OutputValue=SelfFileInput(locator, EPOCH))
            ordinary = MakeBareImport(neutral, recipe, plan, AmbientValue=MakeImportLight(EPOCH))
            bare = MakeLocalPrism(neutral.brep)
            require(EncodeLocalBody(case["feature"], bare) == ordinary.StreamsValue[KLocalBodyStream],
                    "isolated tolerance source does not match the shared local body")
            meters = case["tolerance_mm"] / KMillimetersPerMeter
            require(isfinite(meters) and meters > 0, "local tolerance must be a finite positive length")
            selected = [node for node in bare if node.KindValue in KIND_OWNERS]
            require(len(selected) == 26 and all(node.FieldsValue["tolerance"] == KMissingParam for node in selected),
                    "ordinary topology already carries a separate tolerance")
            nodes = tuple(replace(node, FieldsValue=dict(node.FieldsValue, tolerance=meters))
                          if node.KindValue in KIND_OWNERS else node for node in bare)
            before, after = EncodeLocalXmt(bare), EncodeLocalXmt(nodes)
            streams = dict(ordinary.StreamsValue)
            streams[KLocalBodyStream] = EncodeLocalBody(case["feature"], nodes)
            blob = BuildSldprt(streams, FormatVersion=4)
        require(not accesses, "guard recorded a runtime data, CAD, or process access")
        parsed = SldprtArchive.from_bytes(blob)
        require(parsed.streams == streams and {key for key, value in streams.items() if value != ordinary.StreamsValue[key]}
                == {KLocalBodyStream}, "tolerance changed an unowned archive stream")
        read, _ = ReadLocalNodes(after)
        require(tuple(read.values()) == nodes, "typed tolerance transmit changed after decode")
        proof = inspect_part(blob, case | {"tolerance_m": meters}, name, warm=False)
        require(proof["kernel"] == artifact(after) and proof["feature_id"] == ordinary.FeatureValue.FieldsValue["f08"]
                and proof["atom_id"] == ordinary.AtomId, "complete part lost its model-derived transmit or owner identity")
        output[name] = {"tolerance_m": meters, "proof": proof, "baseline_part": artifact(ordinary.BytesValue),
                        "baseline_kernel": artifact(before), "changed_stream": KLocalBodyStream,
                        "streams": {key: artifact(value) for key, value in streams.items()},
                        "candidate": b64encode(blob).decode()}
    return output


def stage(args):
    revision = args.revision
    require(git("rev-parse", "--verify", f"{revision}^{{commit}}").decode().strip() == revision
            and git("rev-parse", f"{revision}^").decode().strip() == BASE
            and git("rev-parse", f"{revision}:src").decode().strip() == SDK_TREE,
            "use the exact committed research-only child of the pinned aggregate")
    expected_tools = [(revision, BUILDER), (revision, OBSERVER), *((BASE, name) for name in SOURCE_TOOLS)]
    for ref, name in expected_tools:
        require((HERE / name).read_bytes() == git("show", f"{ref}:{RESEARCH}{name}"), "host research closure differs from Git")
    sources = args.sources.resolve(strict=True)
    destination = args.destination.resolve()
    require(not destination.exists() and not destination.is_relative_to(sources)
            and not any((parent / ".git").exists() for parent in destination.parents),
            "use an unused external packet directory separate from the source")
    requests, negative, prior = project(sources)
    with TemporaryDirectory(prefix="kit-baked-tolerance-part-") as scratch:
        archive = git("archive", "--format=tar", revision, "src")
        with open_tar(fileobj=BytesIO(archive)) as tar:
            tar.extractall(scratch, filter="data")
        command = (sys.executable, "-I", "-B", __file__, "worker", str(Path(scratch) / "src"))
        results = [run(command, input=encode(requests), capture_output=True, cwd=scratch, timeout=120) for _ in range(2)]
        require(all(result.returncode == 0 for result in results),
                "\n".join(result.stderr.decode(errors="replace") for result in results if result.returncode))
        require(results[0].stdout == results[1].stdout, "fresh guarded part builders disagree")
    built = json.loads(results[0].stdout)
    files = {}
    for slot, values in built.items():
        original = prior[slot + ".FCStd"]
        require(values["baseline_kernel"]["sha256"] == original["untoleranced_transmit_sha256"]
                and values["proof"]["kernel"] == {"bytes": original["tolerance_transmit_bytes"],
                                                "sha256": original["tolerance_transmit_sha256"]}
                and values["tolerance_m"] == original["encoded_tolerance_m"], "embedded kernel differs from the pinned preflight")
        files[slot] = b64decode(values.pop("candidate"), validate=True)
        require(artifact(files[slot]) == values["proof"]["part"], "generated part identity changed")
        requests[slot].update(values)
    support = {name: git("show", f"{revision if name == OBSERVER else BASE}:{relative}")
               for name, relative in TOOLS.items()}
    control = checked(args.control.resolve(strict=True), CONTROL)
    job = {"schema": JOB_SCHEMA, "method_revision": revision, "sdk_tree": SDK_TREE,
           "oracle_build": BUILD, "oracle_sha256": ORACLE, "guest": GUEST, "phases": PHASES,
           "source_owner_receipt_sha256": OWNER_RECEIPT, "tolerance_receipt_sha256": TOLERANCE_RECEIPT,
           "control": artifact(control), "cases": requests, "editable_source_refused": negative,
           "independent_guarded_processes": 2, "construction_accesses": 0,
           "native_processes": 0, "whole_source_conversions": 0, "heldout_credit": 0,
           "tools": {name: artifact(data) for name, data in support.items()}}
    destination.mkdir()
    (destination / "Tools").mkdir()
    (destination / "Candidates").mkdir()
    for directory, inputs in ((destination / "Tools", support),
                              (destination / "Candidates", {k + ".SLDPRT": v for k, v in files.items()}),
                              (destination, {"Control.SLDPRT": control, "Job.json": encode(job)})):
        for name, data in inputs.items():
            with (directory / name).open("xb") as output:
                output.write(data)
    pin = artifact(encode(job))["sha256"]
    observed = check_output((sys.executable, "-I", "-B", str(destination / "Tools" / OBSERVER),
                             str(destination / "Job.json"), "--job-sha256", pin, "--verify-only"), cwd=destination)
    require(json.loads(observed) == {"verified": True, "job_sha256": pin, "native_processes": 0}, "standalone custody failed")
    print(encode({"packet": str(destination), "job_sha256": pin, "method_revision": revision,
                  "candidates": {name: artifact(data) for name, data in files.items()},
                  "guarded_processes": 2, "native_processes": 0}).decode(), end="")


def audit(args):
    packet = args.packet.resolve(strict=True)
    sys.path.insert(0, str(ROOT / "src"))
    require(git("rev-parse", "HEAD:src").decode().strip() == SDK_TREE
            and not git("diff", "HEAD", "--", "src"), "saved readback needs the frozen SDK tree")
    job = verify(packet / "Job.json", args.job_sha256, completed=True, packed_worker=False)
    native_data = checked(packet / "Native.json", args.native_sha256)
    native = json.loads(native_data)
    require(native["schema"] == "kit.sw2026.baked-local-tolerance-native-result.v1"
            and native["job_sha256"] == args.job_sha256 and native["oracle_build"] == BUILD
            and native["oracle_sha256"] == ORACLE and native["heldout_credit"] == native["whole_source_conversions"] == 0
            and set(native["saves"]) <= set(CASES)
            and {path.name for path in (packet / "Saved").iterdir()} == {name + ".SLDPRT" for name in native["saves"]},
            "native receipt or derivative inventory differs from the frozen batch")
    rows = {}
    for name, saved in native["saves"].items():
        require(name in CASES and native["phases"][name]["saved"] == saved, "saved derivative escaped native phase custody")
        blob = checked(packet / "Saved" / (name + ".SLDPRT"), saved["sha256"], saved["bytes"])
        try:
            rows[name] = inspect_part(blob, job["cases"][name], name, warm=True)
            phase = native["phases"][name]["rebuilt"]
            require(rows[name].get("feature_id") == phase["feature_id"] or rows[name]["status"] == "local_group_absent",
                    "typed saved import owner disagrees with the live native ID")
        except (KeyError, OverflowError, ValueError) as exc:
            rows[name] = {"status": "unresolved_saved_layout", "diagnostic": str(exc), "part": artifact(blob)}
    report = {"job_sha256": args.job_sha256, "native_receipt_sha256": args.native_sha256,
              "native_lifecycles_healthy": native["passed"], "controls_healthy": native["controls_healthy"],
              "saved_local_tolerance_exact": native["passed"] and set(rows) == set(CASES)
              and all(row["status"] == "exact" for row in rows.values()),
              "heldout_credit": 0, "whole_source_conversions": 0, "cases": rows}
    encoded = encode(report)
    with args.output.open("xb") as out:
        out.write(encoded)
    print(encoded.decode(), end="")


def main():
    parser = ArgumentParser()
    commands = parser.add_subparsers(dest="mode", required=True)
    worker = commands.add_parser("worker")
    worker.add_argument("sdk", type=Path)
    freeze = commands.add_parser("stage")
    freeze.add_argument("sources", type=Path)
    freeze.add_argument("control", type=Path)
    freeze.add_argument("destination", type=Path)
    freeze.add_argument("--revision", required=True)
    saved = commands.add_parser("audit")
    saved.add_argument("packet", type=Path)
    saved.add_argument("--job-sha256", required=True)
    saved.add_argument("--native-sha256", required=True)
    saved.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.mode == "worker":
        print(encode(construct(args.sdk, json.load(sys.stdin))).decode(), end="")
    elif args.mode == "stage":
        stage(args)
    else:
        audit(args)


if __name__ == "__main__":
    main()
