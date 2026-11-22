from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from json import dumps, loads
from math import isclose
from os import O_RDWR, O_WRONLY
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from convert import open_document, write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.registry import AdapterRegistry
from convert.adapters.registry.RegistryErrors import RegistryError
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import KResolvedFeaturesStream
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.Writing.AttachedBox.BoxTransferCaps import BoxTransferCaps
from convert.adapters.solidworks.Core.Writing.AttachedBox.CanWriteBox import CanWriteBox
from convert.adapters.solidworks.Core.Writing.AttachedBox.EmitBoxMut import EmitBoxMut
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from convert.Commands.WriteReport import WriteReport
from interchange import CadDocument
from interchange.Features.FeaturePlaneAxis import PlaneAxis

FORMAT = "solidworks.sldprt"
SOURCE_SHA = "25c836424406343439bd3fa9acd82f8e6dbabdae689fe2a799099bf73805aafb"
OUTPUT_SHA = "0d4cba0b66e443e487793204dc82985d5206704a0646b63afb1a4c410b1c54cc"
SUMMARY_SHA = "7df283cd1c0ea388f3a0675deb63ef37184eada40ebbd4cd0898628c9996d624"
NATIVE_SHA = "0ac0c750cd671a2f4c5dcc7e3459d79a51199c3c0cd7220ba8cc2dd6a953ac38"
WINDOWS_RECEIPT_SHA = "fa0034fc6150c25888d40e6226aceeb896bd904ad8c98a2e53bb65812f0cd826"
SEMANTIC = {"body_structure", "brep", "configurations", "parameters", "parametric_history", "support_planes"}
EVIDENCE = {"native_payloads", "provenance", "roundtrip_metadata"}
SENTINEL = b"preexisting conversion output"


def digest(data):
    return sha256(data).hexdigest()


def read_locked(path, expected):
    data = path.read_bytes()
    assert digest(data) == expected
    return data


def stream_hashes(payload):
    return {name: {"bytes": len(data), "sha256": digest(data)} for name, data in SldprtArchive.from_bytes(payload).streams.items()}


class Audit:
    def __init__(self, scratch):
        self.scratch = scratch
        self.enabled = False
        self.opens = 0
        self.invalid = []
        sys.addaudithook(self.observe)

    def observe(self, event, args):
        if not self.enabled:
            return
        if event in ("subprocess.Popen", "os.system", "socket.connect", "ctypes.dlopen"):
            self.invalid.append(event)
            raise RuntimeError(event)
        if event == "import" and args[0].split(".")[0] in ("pythoncom", "pywintypes", "win32com", "FreeCAD", "adsk"):
            self.invalid.append(args[0])
            raise RuntimeError(args[0])
        if event == "open":
            path, mode, flags = args
            if isinstance(path, str):
                value = Path(path).absolute()
                if value.is_relative_to(self.scratch):
                    if value.suffix.casefold() == ".sldprt" and flags & (O_WRONLY | O_RDWR):
                        self.opens += 1
                        return
                    if value.name.startswith(".") and ".kit-" in value.name and value.is_dir():
                        return
            self.invalid.append(str(path))
            raise RuntimeError(f"external file open during generation: {path}")

    def run(self, function):
        self.enabled = True
        try:
            return function()
        finally:
            self.enabled = False

    def result(self):
        assert not self.invalid
        return {"runtime_input_reads": 0, "external_launches": 0, "actual_output_opens": self.opens}


def denied(function, phrase):
    try:
        function()
    except (ValueError, TypeError, RegistryError) as error:
        assert phrase in str(error), (phrase, str(error))
        return str(error)
    raise AssertionError("unqualified request changed a destination")


def measure(args):
    summary = read_locked(args.summary, SUMMARY_SHA).decode("utf-8")
    raw = read_locked(args.native_trial, NATIVE_SHA).decode("utf-8")
    manifest = loads(summary)
    return manifest["candidate"]["native_path"], {
        "written_at": manifest["creation_epoch"],
        "receipt": {"summary": summary, "native_result": raw},
    }


def check_source_evidence(result):
    assert result.vendor_loadable and result.application_usable and not result.dropped
    assert not result.requirements and not result.IsRoundtripSafe
    assert {row.capability.value for row in result.transfers} == SEMANTIC
    assert all(row.mode.value == "native" for row in result.transfers)
    evidence = WriteReport(result)["source_evidence"]
    assert evidence["source_sha256"] == SOURCE_SHA and evidence["source_native_byte_replay"] is False
    assert set(evidence["evidence_only_capabilities"]) == EVIDENCE
    assert len(evidence["source_object_order"]) == 9
    assert len(evidence["archive_and_binding"]) == 2
    assert len(evidence["shape_caches"]) == 3
    assert all(len(row["physical_roles"]) == 26 for row in evidence["shape_caches"])
    actual = result.metadata["solidworks_native_measurement"]
    assert actual["generated_sha256"] == OUTPUT_SHA and actual["native_result_sha256"] == NATIVE_SHA


def inspect_box(document, full):
    restored = CadDocument.from_json(document.to_json(indent=None))
    assert restored.to_json(indent=None) == document.to_json(indent=None)
    restored.assert_valid()
    sketch, = restored.sketches
    body, = restored.bodies
    assert len(restored.feature_timeline) == 22
    assert {param.name: param.value.value for param in restored.parameters} == {"Length": 20, "Width": 30, "Height": 10}
    assert len(sketch.parameter_ids) == 2 and len(sketch.constraints) == 7
    assert sketch.attributes["typed_origin_coincidence"] is True
    assert sketch.support_plane_id == "sldprt:plane:15"
    creator, = (row for row in restored.feature_timeline if row.id == body.final_feature_id)
    assert creator.name == "AdditiveBox" and creator.attributes["direction_code"] == 1
    axes = [row for row in restored.feature_timeline if isinstance(row.definition, PlaneAxis)]
    extent = ((-1.0, 21.0), (-10.5, 0.5), (-1.5, 31.5))
    support = ((15, 14), (14, 16), (16, 15))
    selections = {value.id: value for value in restored.selections}
    for index, axis in enumerate(axes):
        assert axis.name == "XYZ"[index] + "-axis"
        assert axis.input_feature_ids == tuple(f"sldprt:feature:{value}" for value in support[index])
        assert axis.selection_ids == (axis.definition.FirstPlaneSelectionId, axis.definition.SecondPlaneSelectionId)
        assert tuple(selections[value].path[0].entity_id for value in axis.selection_ids) == tuple(f"sldprt:plane:{value}" for value in support[index])
        start, end = axis.definition.StartMm, axis.definition.EndMm
        observed = tuple((getattr(start, key), getattr(end, key)) for key in "xyz")
        analytic = tuple(extent[index] if value == index else (0.0, 0.0) for value in range(3))
        assert all(isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12)
                   for pair, planned in zip(observed, analytic, strict=True)
                   for actual, expected in zip(pair, planned, strict=True))
    axis_ids = {value for axis in axes for value in axis.selection_ids}
    assert len(axes) == 3 and len(axis_ids) == 6
    residual, = (value for value in restored.selections if value.id not in axis_ids)
    assert residual.query["topology_role"] == "direction_axis"
    assert residual.query["native_owner_id"] == creator.attributes["native_object_id"]
    assert residual.query["native_target_id"] == sketch.attributes["native_object_id"]
    assert residual.path[0].subelement == "N_Axis"
    counts = body.topology
    assert body.name == "Body" and counts.volume == 6000.0 and counts.surface_area == 2200.0
    assert (counts.solid_count, counts.shell_count, counts.face_count, counts.edge_count, counts.vertex_count) == (1, 1, 6, 12, 8)
    assert counts.bounding_box.minimum.x == 0.0 and counts.bounding_box.minimum.y == -10.0
    assert counts.bounding_box.maximum.x == 20.0 and counts.bounding_box.maximum.z == 30.0
    assert (restored.brep is not None) is full


def crossed_axis(payload):
    archive = SldprtArchive.from_bytes(payload)
    linked = ReadNativeLink(archive, 0)
    roots = linked.ResolvedValue.RootsValue
    (first, second, third) = (node for node in roots if node is not None and node.ClassValue.NameValue == "moRefAxis_c")
    first.FieldsValue["f700"].FieldsValue["f80"] = second.FieldsValue["f700"].FieldsValue["f80"]
    data, _ = WriteResolMut(roots, linked.ResolvedValue.ExtraFields, 19000, linked.ConfigValue.MapValue, linked.ResolvedValue.ContextValue)
    return BuildSldprt({**archive.streams, KResolvedFeaturesStream: data}, FormatVersion=4)


def box_worker(args, scratch):
    locator, receipt = measure(args)
    original = read_locked(args.source, SOURCE_SHA)
    expected = read_locked(args.candidate, OUTPUT_SHA)
    document = open_document(original, source_format="freecad.fcstd", strict=True)
    document = CadDocument.from_json(document.to_json(indent=None))
    assert len(document.feature_timeline) == 1 and len(document.parameters) == 11 and len(document.brep_payloads) == 5
    GetDocumentCaps(document)
    writer = SldprtWriter()
    registry = AdapterRegistry()
    registry.register_writer(writer)
    values = {"require_native_transfers": True, "final_destination": locator, "solidworks_native_measurement": receipt}
    opts = WriteOptions(values=values)
    wrong_path = scratch / "F14c.SLDPRT"
    wrong_path.write_bytes(SENTINEL)
    audit = Audit(scratch)
    methods = {
        "direct": lambda sink: writer.write(document, sink, opts),
        "public": lambda sink: write_document(document, sink, destination_format=FORMAT, values=values, allow_carrier=False),
        "case_insensitive": lambda sink: write_document(document, sink, destination_format=FORMAT.upper(), values=values, allow_carrier=False),
        "registry_explicit": lambda sink: registry.write(document, sink, format_id=FORMAT, options=opts),
        "registry_inferred": lambda sink: registry.write(document, sink, options=opts),
    }
    for action in methods.values():
        sink = BytesIO()
        result = audit.run(lambda: action(sink))
        assert result.bytes_written == len(expected) and sink.getvalue() == expected
        check_source_evidence(result)
    for full in (True, False):
        result = audit.run(lambda: open_document(sink.getvalue(), source_format=FORMAT, strict=True, include_brep=full))
        inspect_box(result, full)
    altered = crossed_axis(sink.getvalue())
    failures = {"crossed_axis_owner": denied(lambda: audit.run(lambda: open_document(altered, source_format=FORMAT, strict=True)), "unverified typed history")}
    for mode, source, settings, message in (
        ("no_measurement", document, {"final_destination": locator}, "offline native measurement"),
        ("foreign_stream_locator", document, {**values, "final_destination": locator + ".other"}, "exact native locator"),
        ("foreign_epoch", document, {**values, "solidworks_native_measurement": {**receipt, "written_at": receipt["written_at"] + 1}}, "bind this intact source"),
        ("rewritten_summary", document, {**values, "solidworks_native_measurement": {**receipt, "receipt": {**receipt["receipt"], "summary": receipt["receipt"]["summary"] + " "}}}, "summary digest differs"),
        ("rewritten_terminal", document, {**values, "solidworks_native_measurement": {**receipt, "receipt": {**receipt["receipt"], "native_result": receipt["receipt"]["native_result"] + " "}}}, "terminal digest differs"),
        ("extra_source_owner", replace(document, metadata={**document.metadata, "other": True}), values, "neutral owners disagree"),
    ):
        rejected = BytesIO()
        failures[mode] = denied(lambda: audit.run(lambda: writer.write(source, rejected, WriteOptions(values=settings))), message)
        assert not rejected.getvalue() and rejected.tell() == 0
    for mode, action in methods.items():
        populated = BytesIO(SENTINEL)
        populated.seek(4)
        failures[mode + "_occupied_sink"] = denied(lambda: audit.run(lambda: action(populated)), "standalone")
        assert populated.getvalue() == SENTINEL and populated.tell() == 4
    for mode, action in (
        ("direct_path", lambda: writer.write(document, wrong_path, replace(opts, overwrite=True))),
        ("public_inferred_path", lambda: write_document(document, wrong_path, overwrite=True, values=values)),
        ("public_explicit_path", lambda: write_document(document, wrong_path, destination_format=FORMAT, overwrite=True, values=values)),
    ):
        failures[mode] = denied(lambda: audit.run(action), "actual final native locator")
        assert wrong_path.read_bytes() == SENTINEL and list(scratch.iterdir()) == [wrong_path]
    return {
        "role": "F14c", "source_sha256": SOURCE_SHA, "archive_sha256": OUTPUT_SHA,
        "bytes": len(expected), "stream_readbacks": 2, "public_stream_routes": list(methods),
        "strict_geometry": {"bodies": 1, "volume_mm3": 6000, "area_mm2": 2200, "ordered_features": 22, "drivers": 3, "axes": 3, "axis_selections": 6},
        "refusals": failures, "streams": stream_hashes(sink.getvalue()), **audit.result(),
    }


def plain_worker(args, scratch):
    label = ("Skew", "Step")[args.worker - 2]
    packet = args.plain_packet / label
    neutral = loads((packet / "SdkRequest.json").read_bytes())
    original = CadDocument.from_json(dumps(neutral["document"]))
    final = scratch / PureWindowsPath(neutral["expected_locator"]).name
    receipt = loads((ROOT / "re/solidworks/measurements/2026/SdkDefaultPartNative01.json").read_bytes())
    record, = (row for row in receipt["builds"] if row["role"] == label)
    expected = read_locked(packet / final.name, record["candidate_sha256"])
    values = {"solidworks_native_measurement": {"written_at": neutral["written_at"], "receipt": receipt}}
    GetDocumentCaps(original)
    audit = Audit(scratch)
    report = audit.run(lambda: write_document(original, final, values=values))
    assert report.vendor_loadable and report.application_usable and final.read_bytes() == expected
    reread = open_document(final, strict=True)
    assert reread.brep is not None and reread.bodies[0].topology.solid_count == 1
    sink = BytesIO()
    settings = WriteOptions(values={**values, "final_destination": neutral["expected_locator"]})
    report = audit.run(lambda: SldprtWriter().write(reread, sink, settings))
    assert report.vendor_loadable and report.application_usable and sink.getvalue() == expected
    return {"role": label, "bytes": len(expected), "archive_sha256": digest(expected), **audit.result()}


def check_cli(args):
    _, receipt = measure(args)
    bootstrap = "import runpy,sys;sys.path.insert(0,sys.argv.pop(1));runpy.run_module('convert',run_name='__main__')"
    with TemporaryDirectory(prefix="KitMainAttachedBoxCli-") as folder:
        scratch = Path(folder)
        output = scratch / "F14c.SLDPRT"
        output.write_bytes(SENTINEL)
        supply = scratch / "Measurement.json"
        supply.write_text(dumps(receipt), encoding="utf-8")
        reports = {}
        for role, flags in (("inferred", []), ("explicit", ["--to", FORMAT])):
            process = run([sys.executable, "-I", "-B", "-c", bootstrap, str(ROOT / "src"), "convert", str(args.source), str(output), *flags, "--native-measurement", str(supply), "--overwrite", "--json"], capture_output=True, check=False, text=True)
            report = loads(process.stderr or process.stdout)
            assert process.returncode == 1 and "actual final native locator" in report["message"]
            assert output.read_bytes() == SENTINEL and sorted(path.name for path in scratch.iterdir()) == sorted([output.name, supply.name])
            reports[role] = report
        return reports


def source_fingerprint():
    listed = check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "src"], cwd=ROOT)
    paths = sorted(set(name for name in listed.split(b"\0") if name))
    result = sha256()
    for name in paths:
        result.update(name + b"\0" + sha256((ROOT / name.decode("utf-8")).read_bytes()).digest())
    return {"files": len(paths), "sha256": result.hexdigest()}


def main():
    parser = ArgumentParser()
    for name in ("source", "candidate", "summary", "native-trial", "plain-packet"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--worker", type=int, choices=range(4))
    args = parser.parse_args()
    if args.worker is not None:
        for codec in ("utf-8-sig", "cp437", "utf-16-le"):
            lookup(codec)
        with TemporaryDirectory(prefix="KitMainAttachedBox-") as temp:
            job = box_worker if args.worker < 2 else plain_worker
            print(dumps(job(args, Path(temp).resolve())))
        return
    rows = [
        loads(check_output([sys.executable, "-I", "-B", str(Path(__file__).resolve()), *sys.argv[1:], "--worker", str(index)]))
        for index in range(4)
    ]
    assert rows[0] == rows[1] and len(rows[0]["streams"]) == 12
    print(dumps({
        "schema": "kit.sw2026.attached-box-main-publication.v1",
        "proof_tool_sha256": digest(Path(__file__).read_bytes()),
        "native_trial_sha256": NATIVE_SHA, "native_summary_sha256": SUMMARY_SHA,
        "prior_aggregate_windows_publication_sha256": WINDOWS_RECEIPT_SHA,
        "readers_and_writers": rows, "cli_wrong_locator": check_cli(args),
        "source_fingerprint": source_fingerprint(),
        "fresh_isolated_workers": len(rows), "new_native_processes": 0,
        "new_heldout_credit": 0, "new_historical_corpus_credit": 0,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
