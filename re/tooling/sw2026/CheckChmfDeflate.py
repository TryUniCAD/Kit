from argparse import ArgumentParser
from base64 import b64decode, b64encode
from codecs import lookup
from contextlib import contextmanager
from dataclasses import replace
from importlib import import_module
from io import BytesIO
from json import dumps, loads
from pathlib import Path, PureWindowsPath
from subprocess import run
from tempfile import TemporaryDirectory
from zlib import ZLIB_RUNTIME_VERSION
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]
from CheckChmfJsonBoundary import JSON, verify_snapshot
from CheckMeasuredChamfer import FORMAT, OPTION, build_request, demand, digest
from CheckScopedPlainWriter import WriterAudit, reject

UNCLAIMED = b"unclaimed transport bytes"


@contextmanager
def alternate_container(enabled=True):
    module = import_module("convert.adapters.solidworks.Container.Container")
    baseline = module.ZlibValue

    class OuterStore:
        def __getattr__(self, name):
            return getattr(baseline, name)

        def compressobj(self, *, level, wbits):
            demand(level == 1 and wbits == -15, "production outer codec declaration changed")
            return baseline.compressobj(level=0, wbits=wbits)

    if enabled:
        module.ZlibValue = OuterStore()
    try:
        yield
    finally:
        module.ZlibValue = baseline


def load_model(request):
    from convert.adapters.base.WriteOptions import WriteOptions
    from interchange.document.Models.DocumentModel import CadDocument

    spec = request["neutral"]
    options = {"final_destination": spec["locator"], OPTION: request["evidence"], "require_native_transfers": True}
    return CadDocument.from_json(dumps(spec["document"])), WriteOptions(values=options)


def fixed_inputs(request):
    from convert.adapters.solidworks.Archive.Construction.Metadata.HistoryInput import HistoryInput
    from convert.adapters.solidworks.Archive.Construction.Metadata.MakeFreshHist import MakeFreshHist
    from convert.adapters.solidworks.Archive.History.WriteHistGraph import WriteHistGraph
    from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
    from convert.adapters.solidworks.Core.Preparation.Chamfers.PrepChmfPart import PrepChmfPart

    model, options = load_model(request)
    epoch = request["neutral"]["epoch"]
    candidate = PrepChmfPart(model, BytesIO(), epoch, options)
    expected = request["case"]
    basename = PureWindowsPath(request["neutral"]["locator"]).name
    measured = ROOT / "re/solidworks/v2026/corpus/chamfer-distance-measured" / basename
    positive = measured.read_bytes()
    demand(digest(positive) == expected["archive_sha256"], "fixed measured input digest changed")
    measured_streams = SldprtArchive.from_bytes(positive).streams
    demand({name: digest(raw) for name, raw in candidate.StreamsValue.items()} == expected["streams"]
           and candidate.StreamsValue == measured_streams, "fixed source streams differ from measured inputs")
    history = WriteHistGraph(MakeFreshHist(HistoryInput(epoch + 1, "Logical comparison", 1, 0, 0, False)), 19000)[0]
    logical = dict(candidate.StreamsValue) | {"_MO_VERSION_19000/History": history}
    changed = BuildSldprt(logical, FormatVersion=4)
    observed = SldprtArchive.from_bytes(changed).streams
    demand(list(name for name in observed if observed[name] != candidate.StreamsValue[name]) == ["_MO_VERSION_19000/History"],
           "negative contains more than the independently generated history stream difference")
    return positive, changed


def bad_snapshots(snapshot, other_sha):
    (body,) = snapshot.bodies
    return (
        ("forged_source_sha", replace(snapshot, source=replace(snapshot.source, sha256="0" * 64)), "source identity"),
        ("other_measured_sha", replace(snapshot, source=replace(snapshot.source, sha256=other_sha),
         metadata=dict(snapshot.metadata) | {"solidworks_source_sha256": other_sha}), "source identity"),
        ("altered_body_volume", replace(snapshot, bodies=(replace(body, topology=replace(body.topology, volume=body.topology.volume + 1)),)),
         "cold chamfer JSON readback differs from its regenerated part"),
    )


def guard_imports():
    for module in ("interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo",
                   "interchange.document.Models.DocumentProvenance", "interchange.document.Models.FilterMetadata", "interchange.document.Validation.DocumentAssemblyValidate",
                   "interchange.document.Validation.DocumentFeatureValidate", "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    for codec in ("ascii", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "latin-1", "cp1252"):
        lookup(codec)


def sdk_worker(job):
    audit = WriterAudit(ROOT / "src", HERE.parent / "ChmfDeflateUnused.SLDPRT")
    sys.addaudithook(audit.observe)
    from convert import open_document, write_document
    from convert.adapters.json.Adapter import JsonAdapter
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Preparation.Chamfers.PrepChmfPart import PrepChmfPart
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
    from interchange.Features.FeatureKinds import NativeFeature

    guard_imports()
    request = job["request"]
    model, options = load_model(request)
    raw, changed = (b64decode(job[name], validate=True) for name in ("original", "changed"))
    audit.phase = "cold"
    reader = lambda value: open_document(value, source_format=FORMAT, strict=True)
    source, stale_stream, unclaimed = reader(raw), reader(changed), reader(raw + UNCLAIMED)
    direct = JsonAdapter().write
    registry = lambda value, sink: write_document(value, sink, destination_format=JSON, allow_carrier=False)
    measured = digest(raw) == request["case"]["archive_sha256"]
    reports = {}
    with alternate_container():
        fresh = PrepChmfPart(model, BytesIO(), request["neutral"]["epoch"], options)
        observed = SldprtArchive.from_bytes(fresh.BytesValue).streams
        demand(fresh.BytesValue != raw and observed == SldprtArchive.from_bytes(raw).streams,
               "alternate physical bytes do not carry the exact ten fixed-original streams")
        targets = (BytesIO(), BytesIO())
        for write, target in zip((direct, registry), targets, strict=True):
            write(source, target)
        wire = targets[0].getvalue()
        demand(wire == targets[1].getvalue(), "JSON routes disagree across outer compression")
        snapshot = open_document(wire, source_format=JSON, strict=True)
        reports["ordered_rows"] = len(snapshot.feature_timeline)
        reports["native_rows"] = verify_snapshot(source, snapshot, wire, NativeFeature)
        reports["snapshot_source_sha256"] = snapshot.source.sha256
        for write in (direct, registry):
            for _, invalid, message in (*bad_snapshots(snapshot if measured else source, job["other_sha"]),
                    ("changed_logical_stream", stale_stream, "source logical streams differ"),
                    ("unclaimed_transport", unclaimed, "source container framing differs"),
                    ("attachment_digest", replace(source, source=replace(source.source, sha256="0" * 64)), "original source identity")):
                sink = BytesIO(b"untouched")
                reject(lambda: write(invalid, sink), ValueError, message)
                demand(sink.getvalue() == b"untouched", "bad JSON input altered a stream")
            repeated = BytesIO()
            if measured:
                write(snapshot, repeated)
                demand(repeated.getvalue() == wire, "fixed measured stripped snapshot differs under alternate compression")
            else:
                reject(lambda: write(snapshot, repeated), ValueError, "source identity")
        native = SldprtWriter()
        for write in (lambda target: native.write(model, target, options),
                      lambda target: write_document(model, target, destination_format=FORMAT, allow_carrier=False, values=options.values)):
            target = BytesIO(b"untouched")
            reject(lambda: write(target), ValueError, "no unique exact native measurement")
            demand(target.getvalue() == b"untouched", "logical parity authorized unmeasured native output")
    demand(not audit.denied and not audit.target_opens, "guarded conversion accessed runtime files")
    audit.phase = "done"
    return reports | {"original_sha256": digest(raw), "alternate_sha256": digest(fresh.BytesValue), "json_sha256": digest(wire),
                      "measured_original": measured, "logical_streams": len(observed), "json_routes": 2,
                      "sdk_refusals": 12, "native_refusals": 2, "runtime_reads": 0}


def cli_child(arguments, alternate):
    from convert.Commands.MainEntry import MainEntry
    from convert.adapters.solidworks.Core.Preparation.Chamfers.BuildChmfPart import BuildChmfPart
    from convert.adapters.solidworks.Core.Preparation.Chamfers.CheckChmfSnap import CheckChmfSnap

    counts = {"compile": 0, "verify": 0}
    watched = {BuildChmfPart.__code__: "compile", CheckChmfSnap.__code__: "verify"}

    def profile(frame, event, _):
        if event == "call" and frame.f_code in watched:
            counts[watched[frame.f_code]] += 1

    sys.argv[:] = [str(HERE), "convert", *arguments]
    sys.setprofile(profile)
    try:
        with alternate_container(alternate):
            return MainEntry()
    finally:
        sys.setprofile(None)
        print("ProofCounts=" + dumps(counts, sort_keys=True), file=sys.stderr)


def launch_cli(source, destination, *, alternate=True):
    mode = "--cli" if alternate else "--normal-cli"
    result = run((sys.executable, "-I", "-B", str(HERE), mode, "--", str(source), str(destination), "--overwrite", "--json"),
                 cwd=ROOT, capture_output=True, text=True, check=False, timeout=60)
    diagnostic, marker, counts = result.stderr.rpartition("ProofCounts=")
    demand(marker, result.stdout + result.stderr)
    return result.returncode, diagnostic, loads(counts)


def cli_proof(request, raw, changed, measured, other_sha):
    from convert import open_document

    with TemporaryDirectory(prefix="KitChmfDeflate.") as folder:
        area = Path(folder)
        source = area / PureWindowsPath(request["neutral"]["locator"]).name
        source.write_bytes(raw)
        target = area / "Qualified.json"
        code, diagnostic, counts = launch_cli(source, target)
        demand(code == 0 and not diagnostic and counts == {"compile": 1, "verify": 1}, diagnostic)
        wire = target.read_bytes()
        snapshot = open_document(target, source_format=JSON, strict=True)
        repeated = area / "Repeated.json"
        code, diagnostic, repeat_counts = launch_cli(target, repeated)
        demand(repeat_counts == counts and (code == 0 and not diagnostic and repeated.read_bytes() == wire if measured
                                           else code == 1 and "source identity" in diagnostic and not repeated.exists()),
               "CLI repeated snapshot did not match its authenticated source policy")
        contrast = area / "HistoryContrast.SLDPRT"
        contrast.write_bytes(changed)
        unclaimed = area / "UnclaimedTransport.SLDPRT"
        unclaimed.write_bytes(raw + UNCLAIMED)
        inputs = [(contrast, "source logical streams differ", True),
                  (unclaimed, "source container framing differs", True)]
        for label, invalid, message in bad_snapshots(snapshot, other_sha):
            invalid_path = area / (label + ".json")
            invalid_path.write_text(invalid.to_json(), encoding="utf-8")
            inputs.append((invalid_path, message, measured or label != "altered_body_volume"))
        for item, message, alternate in inputs:
            code, diagnostic, calls = launch_cli(item, target, alternate=alternate)
            demand(code == 1 and message in diagnostic and calls == counts and target.read_bytes() == wire,
                   "unverified CLI request modified output or bypassed its single owner")
        return {"first_checks": counts, "repeated_checks": repeat_counts, "cli_refusals": len(inputs),
                "cli_repeated_exact": measured}


def supervise(slot):
    request = build_request(slot)
    other_sha = build_request(1 - slot)["case"]["archive_sha256"]
    raw, changed = fixed_inputs(request)
    packet = {"request": request, "original": b64encode(raw).decode(), "changed": b64encode(changed).decode(), "other_sha": other_sha}
    result = run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=dumps(packet), cwd=ROOT,
                 capture_output=True, text=True, check=False, timeout=60)
    demand(result.returncode == 0 and not result.stderr, result.stdout + result.stderr)
    report = loads(result.stdout)
    return {"schema": "kit.sw2026.chamfer-json-deflate-contrast.v1", "runtime": ZLIB_RUNTIME_VERSION,
            "contrast": "outer_deflate_level_zero", "genuine_zlib_ng_contrast": False,
            "native_processes": 0, "slot": slot, **report,
            **cli_proof(request, raw, changed, report["measured_original"], other_sha)}


if __name__ == "__main__":
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--slot", type=int, choices=(0, 1))
    group.add_argument("--worker", action="store_true")
    group.add_argument("--cli", action="store_true")
    group.add_argument("--normal-cli", action="store_true")
    args, flags = parser.parse_known_args()
    if args.cli or args.normal_cli:
        raise SystemExit(cli_child(flags[1:] if flags[:1] == ["--"] else flags, args.cli))
    demand(not flags, "unexpected supplemental worker options")
    result = sdk_worker(loads(sys.stdin.read())) if args.worker else supervise(args.slot)
    print(dumps(result, sort_keys=True))
