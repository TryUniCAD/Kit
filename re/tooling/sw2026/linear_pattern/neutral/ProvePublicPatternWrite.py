from argparse import ArgumentParser
from codecs import lookup
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
import sys
from tarfile import open as open_tar
from tempfile import TemporaryDirectory


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
FIXTURE = HERE.with_name("PublicPatternWriteInputs.json")
FIXTURE_SHA = "5784abcd6ccc6e93feb88463333b5668bf4fd12f18fa2bde5efbfcc1ccabcdef"
DEFAULTS = ROOT / "re/solidworks/measurements/2026/SharedLinearPatternDefaults01.json"
DEFAULTS_SHA = "ef52c12bc4a22a0de666b043ad586871a0bdfa03e877ac62e591b40dfbaa2df7"
BASE = "e393f3080141976513fe0f397d7766b97879a63c"
FORMAT = "solidworks.sldprt"
POLICY = {"allow_carrier": False, "require_native_transfers": True}
PRODUCTION = ROOT / "src/convert/adapters/solidworks/Core"
CHANGED = ("Preparation/Patterns/IsPatPart.py", "Preparation/Patterns/PatCandidate.py",
           "Preparation/Patterns/PrepPatPart.py", "Preparation/PrepareNative.py",
           "Writing/CanWritePart.py", "Writing/CanWritePat.py", "Writing/SldprtWriter.py")
STOCK_PROOF = ROOT / "re/tooling/sw2026/throughsource/twostockgraph/ProveQualifiedStocks.py"
GUARD = ROOT / "re/tooling/sw2026/VerifySdkCircleEndRegistration.py"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def encode(data):
    return (json.dumps(data, sort_keys=True, allow_nan=False, indent=2) + "\n").encode()


def digest(data):
    return sha256(data).hexdigest()


def locked(path, pin):
    data = path.read_bytes()
    require(digest(data) == pin, "incorrect public fixture authority: " + path.name)
    return json.loads(data)


def compile_expected(document, target):
    from convert.adapters.solidworks.Archive.Construction.Patterns.Emission.EmitPatArchive import EmitPatArchive
    from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.MakePatGraph import MakePatGraph
    from convert.adapters.solidworks.Core.Preparation.Patterns.PlanLinPattern import PlanLinPattern

    return EmitPatArchive(MakePatGraph(PlanLinPattern(document, target)))


def checked_refusal(error_type, expected, action):
    try:
        action()
    except error_type as error:
        require(expected in str(error), "unexpected refusal: " + str(error))
    else:
        raise ValueError("unsupported input reached publication: " + expected)


def change_pitch(document, metres):
    step = document.feature_timeline[-1]
    pitch = next(value for value in document.parameters if value.id == step.parameter_ids[1])
    value = replace(pitch.value, value=metres)
    edited = replace(step, definition=replace(step.definition, spacing=value))
    parameters = tuple(replace(parameter, value=value) if parameter is pitch else parameter
                       for parameter in document.parameters)
    result = replace(document, parameters=parameters, feature_timeline=(*document.feature_timeline[:-1], edited))
    require(not result.validate(), "the unsupported footprint must still be a valid portable feature graph")
    return result


def read_typed(archive, document):
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
    from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.BuildColdPat import BuildColdPat
    from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.ReadPatStocks import ReadPatStocks
    from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadPatOwner import ReadPatOwner
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName

    link = ReadNativeLink(archive, 0)
    header = ReadHeaderGraph(archive.require("Header2"), 19000)
    owner = ReadPatOwner(link, header, IsCold=True)
    stock = ReadPatStocks(link, owner)
    geometry = BuildColdPat(link, owner, stock, document.bodies[0].id)
    topology = geometry.TopologyValue
    source = document.feature_timeline[-1].definition
    require(ReadNativeName(owner.NodeValue) == document.feature_timeline[-1].name
            and owner.DatumValue.TiltValue is not None
            and owner.DatumValue.ReversedValue == source.reversed
            and owner.DriversValue[0].LiveValue == source.instance_count
            and owner.DriversValue[1].LiveValue == source.spacing.value
            and topology.solid_count == 1
            and topology.face_count == document.bodies[0].topology.face_count
            and topology.vertex_count == document.bodies[0].topology.vertex_count,
            "linked native pattern lost its typed feature, drivers or one joined body")
    model = link.ConfigValue.RootValue.FieldsValue
    catalog = model["fa48"].FieldsValue
    names = [row["o"].FieldsValue["f358"] for row in NativeRows(catalog["items"])]
    require(names == ["*Top", "*Back"] and link.ResolvedValue.ExtraFields is None,
            "ordinary writer lost its modeled annotations or introduced a stored body")
    return geometry.BrepValue, topology


def strict_geometry(source, expected, *, format_id=None):
    from convert import open_document
    from interchange import CadDocument

    restored = open_document(source, source_format=format_id, strict=True)
    require(not restored.validate() and restored.brep is not None and len(restored.bodies) == 1
            and restored.bodies[0].topology == expected,
            "strict public read disagrees with the linked geometry")
    require(CadDocument.from_json(restored.to_json()).bodies[0].topology == expected,
            "strict geometry did not survive portable JSON")


def positive(folder, document, target, writer, audit):
    from convert import open_document
    from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative

    config, = document.configurations
    name = PureWindowsPath(target.PathName).name
    path = folder / "body" / name
    staged = folder / "staged" / name
    logical = str(path) if PureWindowsPath(str(path)).drive else rf"C:\KitSdkCandidates\{name}"
    stream_values = {**POLICY, "final_destination": target.PathName}
    unmodified = BytesIO()
    with audit.active("memory"):
        expected_path, file_bytes = compile_expected(document, SelfFileInput(logical, target.SavedAt))
        expected_stream, stream_bytes = compile_expected(document, target)
        require(writer.supports(document, path) and writer.supports(document, unmodified)
                and not writer.supports(document, path.with_name("Renamed.SLDPRT")),
                "selection changed the model or target contract")
        streams = tuple(PrepareNative(
            document, unmodified, target.SavedAt, WriteOptions(configuration=config_value, values=stream_values),
        ) for config_value in (config.id, config.name))
        paths = (
            PrepareNative(document, path, target.SavedAt, WriteOptions(configuration=config.name, values=POLICY)),
            PrepareNative(document, staged, target.SavedAt, WriteOptions(configuration=config.id,
                          values={**POLICY, "final_destination": str(path)})),
        )
        archive = SldprtArchive.from_bytes(stream_bytes)
        require(all(candidate.BytesValue == stream_bytes for candidate in streams)
                and all(candidate.BytesValue == file_bytes for candidate in paths)
                and archive.streams == expected_stream and len(expected_stream) == 10
                and SldprtArchive.from_bytes(file_bytes).streams == expected_path
                and unmodified.getvalue() == b"" and unmodified.tell() == 0
                and not path.exists() and not staged.parent.exists(),
                "ordinary pure preparation changed the independent archive or touched the target")
        body, topology = read_typed(archive, document)
        metadata = open_document(BytesIO(stream_bytes), source_format=FORMAT, strict=True, include_brep=False)
        require(metadata.brep is None and metadata.configurations[0].name == config.name,
                "ordinary metadata reader lost the active configuration")
        strict_geometry(BytesIO(stream_bytes), topology, format_id=FORMAT)
    path.parent.mkdir()
    with audit.active("path"):
        require(path.write_bytes(file_bytes) == len(file_bytes), "short internal research artifact")
    require(path.read_bytes() == file_bytes and tuple(path.parent.iterdir()) == (path,),
            "internal artifact differs from the complete prepared archive")
    strict_geometry(path, topology)
    source = document.feature_timeline[-1].definition
    return {"configuration": config.name, "count": source.instance_count, "pitch_m": source.spacing.value,
            "reversed": source.reversed, "faces": topology.face_count, "logical_streams": len(expected_stream),
            "stream_bytes": len(stream_bytes), "stream_sha256": digest(stream_bytes), "same_locator_file_sha256": digest(file_bytes),
            "intended_capabilities": sorted(value.value for value in GetDocumentCaps(document)),
            "strict_path_and_stream": True, "prepared_routes": 4, "publication_routes": 0}, path, body


def negative(folder, document, target, writer, adapter, audit, path, brep):
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.registry.RegistryErrors import NotFoundError
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative

    policy = {**POLICY, "final_destination": target.PathName}
    other = folder / "absent" / path.name
    config_target = folder / "unpublished-configuration" / path.name
    prior = path.read_bytes()
    payload = BytesIO(b"caller data")
    payload.seek(2)
    options = WriteOptions(overwrite=True, values=policy)
    refusals = (
        ("overlapping", change_pitch(document, .00001), "must remain strictly separated"),
        ("overhanging", change_pitch(document, 1.0), "must all be wholly interior"),
        ("retained_geometry", replace(document, brep=brep), "without additional geometry"),
    )
    with audit.active("memory"):
        for label, candidate, diagnostic in refusals:
            require(not writer.supports(candidate, path) and not writer.supports(candidate, payload),
                    "selection accepted " + label)
            checked_refusal(ValueError, diagnostic,
                            lambda: PrepareNative(candidate, payload, target.SavedAt, options))
            checked_refusal(NotFoundError, "does not support the destination",
                            lambda: write_document(candidate, other, destination_format=FORMAT,
                                                   overwrite=True, allow_carrier=False, values=POLICY))
            checked_refusal(NotFoundError, "does not support the destination",
                            lambda: adapter.write(candidate, path, options))
            checked_refusal(NotFoundError, "does not support the destination",
                            lambda: write_document(candidate, payload, destination_format=FORMAT,
                                                   allow_carrier=False, values=policy))
            checked_refusal(NotFoundError, "does not support the destination",
                            lambda: adapter.write(candidate, payload, options))
        checked_refusal(ValueError, "requested pattern write configuration is unavailable",
                        lambda: PrepareNative(document, payload, target.SavedAt,
                                               WriteOptions(configuration="Other", values=policy)))
        checked_refusal(ValueError, "unnamed native streams require an explicit final destination",
                        lambda: PrepareNative(document, payload, target.SavedAt, WriteOptions(values=POLICY)))
        checked_refusal(ValueError, "unsupported plain part preparation options",
                        lambda: PrepareNative(document, payload, target.SavedAt,
                                               WriteOptions(values={**policy, "invented": True})))
        wrong = {**policy, "final_destination": rf"D:\KitSdkCandidates\{path.name}"}
        checked_refusal(ValueError, "exact authored native basename and event",
                        lambda: PrepareNative(document, payload, target.SavedAt, WriteOptions(values=wrong)))
        for location in (path, config_target):
            checked_refusal(ValueError, "requested pattern write configuration is unavailable",
                            lambda: PrepareNative(document, location, target.SavedAt,
                                                   WriteOptions(configuration="Other", overwrite=True, values=POLICY)))
    require(not other.parent.exists() and not config_target.parent.exists()
            and path.read_bytes() == prior and tuple(path.parent.iterdir()) == (path,)
            and payload.getvalue() == b"caller data" and payload.tell() == 2,
            "refused input left a stage or touched the caller's file or stream")
    return [*(label for label, _, _ in refusals), "configuration", "unnamed_stream", "unmodeled_option", "wrong_locator"]


def worker(folder):
    sys.path[:0] = [str(ROOT / "src"), str(HERE.parents[2])]
    from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
    from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
    from convert.api.ApiContext import GetRegistry
    from interchange import CadDocument, PlaneAxis
    from VerifySdkCircleEndRegistration import OutputGuard
    from RequirePartReceipt import measure_refusals

    job = json.load(sys.stdin)
    document = CadDocument.from_json(encode(job["document"]).decode())
    target = SelfFileInput(**job["target"])
    require(type(document.feature_timeline[2].definition) is PlaneAxis
            and document.brep is None and not document.brep_payloads and not document.validate(),
            "expected complete portable axis, history and no persisted native body")
    for code in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        lookup(code)
    for module in ("interchange.brep.Validation.BrepValidate",
                   "interchange.document.Models.DocumentProvenance",
                   "interchange.document.Validation.DocumentValidate",
                   "interchange.document.Validation.DocumentAssemblyValidate",
                   "interchange.document.Validation.DocumentFeatureValidate",
                   "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    writer = GetRegistry().GetWriter(FORMAT)
    adapter = SldprtAdapter()
    audit = OutputGuard(folder, PureWindowsPath(target.PathName).name)
    sys.addaudithook(audit.audit)
    visible, path, body = positive(folder, document, target, writer, audit)
    visible["refusals"] = negative(folder, document, target, writer, adapter, audit, path, body)
    visible["missing_receipt_refusals"] = measure_refusals(document, path, target.PathName, adapter, audit)
    require(not audit.denied and not any(name in ("Swapp", "pythoncom", "FreeCAD", "adsk")
                or name.startswith("win32com") for name in sys.modules),
            "normal publication attempted a CAD process or runtime input read")
    return {**visible, "runtime_input_file_reads": len(audit.denied), "staging_events": dict(audit.events)}


def legacy_worker(profile, sdk):
    report = run((sys.executable, "-I", "-B", str(STOCK_PROOF), "--worker", profile, "--sdk", str(sdk)),
                 capture_output=True, timeout=90, check=False, cwd=ROOT)
    require(report.returncode == 0 and not report.stderr, profile + " control failed\n" + report.stderr.decode())
    return report.stdout


def legacy_controls():
    modes = ("blind", "circle", "equation", "import", "independent")
    with TemporaryDirectory(prefix="KitPublicPatternBase.") as temp:
        base = Path(temp).resolve()
        package = check_output(("git", "archive", BASE, "src"), cwd=ROOT)
        with open_tar(fileobj=BytesIO(package)) as archive:
            archive.extractall(base, filter="data")
        with ThreadPoolExecutor(max_workers=4) as pool:
            jobs = {profile: (pool.submit(legacy_worker, profile, base / "src"),
                              pool.submit(legacy_worker, profile, ROOT / "src")) for profile in modes}
            results = {}
            for profile, (previous, current) in jobs.items():
                measured = current.result()
                require(measured == previous.result(), "legacy route bytes or transfer evidence changed: " + profile)
                results["two_stock" if profile == "independent" else profile] = {
                    "report_sha256": digest(measured), "artifact_sha256": json.loads(measured)["artifact"]["sha256"]}
    return {"isolated_processes": 2 * len(modes), "existing_probe_sha256": digest(STOCK_PROOF.read_bytes()),
            "base_and_candidate_exact": results}


def measure(exact_host, compare_base):
    jobs = locked(FIXTURE, FIXTURE_SHA)
    previous = locked(DEFAULTS, DEFAULTS_SHA)["cases"]
    results = {}
    with TemporaryDirectory(prefix="KitPublicPattern.") as temp:
        root = Path(temp).resolve()
        for name, job in sorted(jobs.items()):
            home = root / name
            home.mkdir()
            proc = run((sys.executable, "-I", "-B", str(HERE), "--worker", str(home)),
                       input=encode(job), capture_output=True, timeout=60, check=False, cwd=ROOT)
            require(proc.returncode == 0 and not proc.stderr, "public pattern worker failed\n" + proc.stderr.decode())
            row = json.loads(proc.stdout)
            row["historic_host_digest_matches"] = (
                row["stream_sha256"] == previous[name]["complete_file_sha256"]
                and row["stream_bytes"] == previous[name]["complete_bytes"]
            )
            require(not exact_host or row["historic_host_digest_matches"], "complete disclosed host bytes changed")
            results[name] = row
    require(len(results) == 2 and len({row["stream_sha256"] for row in results.values()}) == 2,
            "expected two independent portable part controls")
    return {"schema": "kit.sw2026.oblique-pattern-preparation-gate.v1", "base_revision": BASE,
            "disclosed_neutral_manifest_sha256": FIXTURE_SHA, "historical_host_defaults_sha256": DEFAULTS_SHA,
            "historical_host_digest_required": exact_host, "guarded_worker_processes": len(results),
            "source_sha256": {str((PRODUCTION / path).relative_to(ROOT)): digest((PRODUCTION / path).read_bytes())
                              for path in CHANGED},
            "proof_sha256": digest(HERE.read_bytes()), "output_guard_sha256": digest(GUARD.read_bytes()),
            "legacy": legacy_controls() if compare_base else None, "protected_inputs_read": 0,
            "native_processes_started": 0, "new_native_acceptance": 0, "cases": results}


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--exact-host", action="store_true")
    parser.add_argument("--legacy-base", action="store_true")
    args = parser.parse_args()
    result = worker(args.worker) if args.worker is not None else measure(args.exact_host, args.legacy_base)
    sys.stdout.buffer.write(encode(result))


if __name__ == "__main__":
    main()
