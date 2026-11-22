from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from dataclasses import replace
from io import BytesIO
import json
from os import name as os_name
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from VerifyAttachedAxisRead import NATIVE_TRIAL
from VerifyAttachedBoxAxes import SOURCE_SHA, intake
from VerifyOriginalFcstdAttachedBox import FORMAT, ROOT, digest, guarded, locked, prewarm, require
from convert import open_document, write_document
from convert.adapters.base.SourceEvidenceKey import KSourceEvidence
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.registry import AdapterRegistry
from convert.adapters.registry.RegistryErrors import RegistryError
from convert.adapters.solidworks import SldprtAdapter
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Writing.AttachedBox.BoxTransferCaps import BoxTransferCaps
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import KPartMeasureOpt
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from convert.api.ApiContext import GetRegistry
from convert.Commands.WriteReport import WriteReport
from interchange import CadDocument


BASE = "affae4f56442dfba5d9a14b57db7f63e70344133"
SUMMARY_SHA = "7df283cd1c0ea388f3a0675deb63ef37184eada40ebbd4cd0898628c9996d624"
SENTINEL = b"owned existing conversion target"
LOCATOR_ERROR = "measured attached box requires its actual final native locator"
STREAM_ERROR = "measured attached box stream requires its exact native locator"
SEMANTIC_CAPS = {"body_structure", "brep", "configurations", "parameters", "parametric_history", "support_planes"}
SOURCE_ONLY = {"native_payloads", "provenance", "roundtrip_metadata"}
BOOTSTRAP = "import runpy,sys;sys.path.insert(0,sys.argv.pop(1));runpy.run_module('convert',run_name='__main__')"


def request_values(measurement, locator):
    return {"require_native_transfers": True, "final_destination": locator, KPartMeasureOpt: measurement}


def same_evidence(result, source_sha, measured_sha):
    require(result.application_usable and result.vendor_loadable and not result.dropped and not result.requirements
            and result.roundtrip_safe is False
            and {item.capability.value for item in result.transfers} == SEMANTIC_CAPS
            and all(item.mode.value == "native" and item.carrier_reason is None for item in result.transfers),
            "actual publication did not account for all represented source semantics")
    require(result.MetadataMap[KPartMeasureOpt]["generated_sha256"] == measured_sha
            and result.MetadataMap[KPartMeasureOpt]["native_result_sha256"] == NATIVE_TRIAL,
            "positive publication has wrong measured custody")
    evidence = WriteReport(result)["source_evidence"]
    require(evidence["source_sha256"] == source_sha and set(evidence["evidence_only_capabilities"]) == SOURCE_ONLY
            and evidence["source_native_byte_replay"] is False
            and {item["property"] for item in evidence["shape_caches"]} == {"Shape", "AddSubShape"}
            and len(evidence["shape_caches"]) == 3
            and all(len(item["physical_roles"]) == 26 for item in evidence["shape_caches"])
            and len(evidence["archive_and_binding"]) == 2 and len(evidence["source_object_order"]) == 9
            and len(evidence["native_geometry"]["axes"]) == 3 and len(evidence["native_geometry"]["planes"]) == 3,
            "public result lost actual source evidence and object identities")
    return evidence


def negative(action, diagnostic):
    try:
        action()
    except (ValueError, RegistryError) as error:
        require(diagnostic in str(error), f"unexpected refusal {type(error).__name__}: {error}")
        return str(error)
    raise ValueError("unqualified output reached its destination")


def bound_mutation(measurement, mutate):
    changed = deepcopy(measurement)
    envelope = changed["receipt"]
    result = json.loads(envelope["native_result"])
    summary = json.loads(envelope["summary"])
    mutate(summary, result)
    raw = json.dumps(result, allow_nan=False)
    envelope["native_result"] = raw
    summary["raw_evidence_sha256"]["Result.json"] = digest(raw.encode())
    envelope["summary"] = json.dumps(summary, allow_nan=False)
    return changed


def negative_streams(source, values, locator):
    original = values[KPartMeasureOpt]
    rejected = {}
    for name, selected, expected in (
        ("no_receipt", {k: v for k, v in values.items() if k != KPartMeasureOpt},
         "requires an offline native measurement receipt"),
        ("foreign_logical_locator", {**values, "final_destination": locator + "-other"}, STREAM_ERROR),
        ("changed_epoch", {**values, KPartMeasureOpt: {**original, "written_at": original["written_at"] + 1}},
         "does not bind this intact source"),
        ("rewritten_summary_identical_data", {**values, KPartMeasureOpt: {
            **original, "receipt": {**original["receipt"], "summary": original["receipt"]["summary"] + " "}}},
         "summary digest differs"),
        ("changed_native_terminal", {**values, KPartMeasureOpt: {
            **original, "receipt": {**original["receipt"], "native_result": original["receipt"]["native_result"] + " "}}},
         "terminal digest differs"),
        ("rewritten_control_observation", request_values(bound_mutation(original, lambda summary, raw:
            raw["phases"]["before"].update(passed=False)), locator), "summary digest differs"),
        ("rewritten_numeric_state", request_values(bound_mutation(original, lambda summary, raw:
            raw["phases"]["generated"]["observations"].pop("Length")), locator), "summary digest differs"),
        ("rewritten_axis_extent", request_values(bound_mutation(original, lambda summary, raw:
            raw["phases"]["generated"]["observations"]["Width"]["axes"]["Z-axis"]["endpoints_m"][1].__setitem__(2, .03885)),
            locator), "summary digest differs"),
        ("different_complete_digest", request_values(bound_mutation(original, lambda summary, raw:
            (summary["candidate"].update(sha256="1"*64), raw.update(candidate_sha256="1"*64))), locator),
         "summary digest differs"),
        ("foreign_source_identity", request_values(bound_mutation(original, lambda summary, raw:
            summary.update(source_sha256="2"*64)), locator), "summary digest differs"),
    ):
        sink = BytesIO()
        denied = negative(lambda: write_document(source, sink, destination_format=FORMAT,
                                                  values=selected, allow_carrier=False), expected)
        require(sink.getvalue() == b"" and sink.tell() == 0, "refused measured stream changed caller state")
        rejected[name] = denied
    payloads = source.brep_payloads
    foreign = replace(source, brep_payloads=(replace(payloads[0], data=payloads[2].data, sha256=payloads[2].sha256), *payloads[1:]))
    for name, selected in (
        ("crossed_original_cache", foreign),
        ("other_functional_owner", replace(source, metadata={**source.metadata, "additional_visibility": False})),
    ):
        target = BytesIO(SENTINEL)
        target.seek(4)
        rejected[name] = negative(lambda: SldprtWriter().write(selected, target, WriteOptions(values=values)),
                                  "disagree with its archive")
        require(target.getvalue() == SENTINEL and target.tell() == 4, "malformed source mutated caller state")
    for name, write in (
        ("nonempty_registry_stream", lambda target: write_document(source, target, destination_format=FORMAT, values=values)),
        ("nonempty_direct_stream", lambda target: SldprtWriter().write(source, target, WriteOptions(values=values))),
    ):
        sink = BytesIO(SENTINEL)
        sink.seek(4)
        rejected[name] = negative(lambda: write(sink), "standalone")
        require(sink.getvalue() == SENTINEL and sink.tell() == 4, "whole-stream refusal mutated caller state")
    return rejected


def worker(request):
    for codec in ("utf-8-sig", "cp437"):
        lookup(codec)
    prewarm()
    with TemporaryDirectory(prefix="KitAttachedPublish.") as folder:
        output = Path(folder) / "F14c.SLDPRT"
        output.write_bytes(SENTINEL)
        values = request_values(request["measurement"], request["locator"])
        opts = WriteOptions(overwrite=True, values=values)
        registry = AdapterRegistry()
        registry.register_writer(SldprtWriter())
        with guarded():
            parsed = CadDocument.from_json(request["document"])
            require(type(GetRegistry().select_writer(parsed, output)) is SldprtWriter,
                    "default registry could not select the original source's format by its destination")
            entrypoints = {
                "default_sdk_registry": lambda sink: write_document(parsed, sink, destination_format=FORMAT, values=values, allow_carrier=False),
                "default_sdk_registry_casefolded": lambda sink: write_document(parsed, sink, destination_format=FORMAT.upper(), values=values, allow_carrier=False),
                "direct_part_writer": lambda sink: SldprtWriter().write(parsed, sink, opts),
                "direct_adapter": lambda sink: SldprtAdapter().write(parsed, sink, opts),
                "lowercase_registry_explicit": lambda sink: registry.write(parsed, sink, format_id=FORMAT, options=opts),
                "lowercase_single_writer_inferred": lambda sink: registry.write(parsed, sink, options=opts),
            }
            archives = {}
            original = None
            source_accounting = None
            for role, write in entrypoints.items():
                sink = BytesIO()
                report = write(sink)
                output_bytes = sink.getvalue()
                require(len(output_bytes) == report.bytes_written and digest(output_bytes) == request["output_sha256"],
                        "public writer emitted different measured bytes")
                if original is None:
                    original = output_bytes
                    source_accounting = same_evidence(report, parsed.source.sha256, request["output_sha256"])
                require(original == output_bytes and same_evidence(report, parsed.source.sha256, request["output_sha256"]) == source_accounting,
                        "ordinary writer and adapter did not preserve source accounting")
                archives[role] = digest(output_bytes)
            saved = SldprtArchive.from_bytes(original)
            generated_doc = open_document(original, source_format=FORMAT, strict=True)
            require(len(generated_doc.feature_timeline) == 22 and len(generated_doc.parameters) == 3
                    and len(generated_doc.bodies) == 1 and generated_doc.bodies[0].topology.volume == 6000.0,
                    "normal public result disagrees with proved reader")
            contrasts = negative_streams(parsed, values, request["locator"])
            paths = {
                "direct_spoofed_path": negative(lambda: SldprtWriter().write(parsed, output, opts), LOCATOR_ERROR),
                "registry_inferred_path": negative(lambda: write_document(parsed, output, overwrite=True, values=values,
                                                                          allow_carrier=False), LOCATOR_ERROR),
                "registry_explicit_path": negative(lambda: write_document(parsed, output, destination_format=FORMAT,
                                                                          overwrite=True, values=values, allow_carrier=False), LOCATOR_ERROR),
            }
        require(output.read_bytes() == SENTINEL and list(output.parent.iterdir()) == [output],
                "refused publication kept an unexpected filesystem entry")
    return {"public_stream_sha256": archives, "source_evidence": source_accounting,
            "path_refusals": paths, "stream_and_source_refusals": contrasts,
            "streams": {name: {"bytes": len(value), "sha256": digest(value)} for name, value in saved.streams.items()},
            "strict_readback": {"volume_mm3": 6000, "axes": 3, "drivers": 3, "feature_roots": 22},
            "runtime_input_file_reads": 0}


def cli_check(source, measure):
    with TemporaryDirectory(prefix="KitAttachedCli.") as folder:
        root = Path(folder)
        output = root / "F14c.SLDPRT"
        output.write_bytes(SENTINEL)
        receipt = root / "Measurement.json"
        receipt.write_text(json.dumps(measure, allow_nan=False), encoding="utf-8")
        reports = {}
        for name, flags in (("inferred", []), ("explicit", ["--to", FORMAT])):
            result = subprocess.run([sys.executable, "-I", "-B", "-c", BOOTSTRAP, str(ROOT / "src"),
                                     "convert", str(source), str(output), *flags, "--native-measurement", str(receipt),
                                     "--overwrite", "--json"], capture_output=True, text=True, timeout=120)
            mapped = json.loads(result.stderr or result.stdout)
            require(result.returncode == 1 and mapped == {"error": "ValueError", "message": LOCATOR_ERROR}
                    and output.read_bytes() == SENTINEL and sorted(child.name for child in root.iterdir()) ==
                    ["F14c.SLDPRT", "Measurement.json"], "CLI failed outside the exact physical locator check")
            reports[name] = mapped
        return reports


def changed_paths():
    src = ROOT / "src/convert"
    adapters = src / "adapters"
    sw = adapters / "solidworks/Core/Writing"
    return (
        HERE, *sorted((sw / "AttachedBox").glob("*.py")),
        *(sw / (name + ".py") for name in ("CanWritePart", "CanWriteSldDoc", "SldprtWriter")),
        *(adapters / relative for relative in (
            "Staging/PathStaging.py", "Staging/StageFileScope.py", "base/CapabilityView.py",
            "base/WritePolicy.py", "base/SourceEvidenceKey.py", "registry/RegistryWriteApi.py")),
        src / "Commands/ConvertFile.py", src / "Commands/WriteReport.py",
    )


def main():
    if sys.argv[1:] == ["--worker"]:
        print(json.dumps(worker(json.load(sys.stdin)), allow_nan=False, sort_keys=True))
        return
    require(os_name != "nt", "this host evidence intentionally exercises physical locator refusal")
    parser = ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("summary", type=Path)
    parser.add_argument("native_trial", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--measurement-out", type=Path)
    args = parser.parse_args()
    source, _ = intake(args.source, SOURCE_SHA)
    summary_text = locked(args.summary, SUMMARY_SHA).decode("utf-8")
    summary = json.loads(summary_text)
    native = locked(args.native_trial, NATIVE_TRIAL).decode("utf-8")
    candidate = locked(args.candidate, summary["candidate"]["sha256"])
    measure = {"written_at": summary["creation_epoch"], "receipt": {"summary": summary_text, "native_result": native}}
    request = {"document": source.to_json(), "measurement": measure, "locator": summary["candidate"]["native_path"],
               "output_sha256": summary["candidate"]["sha256"]}
    reports = []
    for _ in range(2):
        ran = subprocess.run([sys.executable, "-I", "-B", str(HERE), "--worker"], input=json.dumps(request, allow_nan=False),
                             capture_output=True, text=True, timeout=120)
        require(ran.returncode == 0 and not ran.stderr, ran.stderr or "guarded publication worker failed")
        reports.append(json.loads(ran.stdout))
    require(reports[0] == reports[1], "guarded restoration and writer transactions differ")
    checked = {name: {"bytes": len(value), "sha256": digest(value)}
               for name, value in SldprtArchive.from_bytes(candidate).streams.items()}
    require(checked == reports[0]["streams"], "normal SDK emitted different streams")
    cli_reports = cli_check(args.source, measure)
    if args.measurement_out is not None:
        with args.measurement_out.open("x", encoding="utf-8") as stream:
            json.dump(measure, stream, allow_nan=False)
            stream.write("\n")
    result = {"schema": "kit.sw2026.attached-box-axes-publication.v1", "base": BASE, "passed": True,
              "native_summary_sha256": SUMMARY_SHA, "native_terminal_sha256": NATIVE_TRIAL,
              "source_sha256": SOURCE_SHA, "fresh_guarded_workers": 2, "native_locator": request["locator"],
              "all_compared_streams": len(checked), "host_cli_physical_locator_refusals": cli_reports,
              "changed_files_sha256": {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in changed_paths()},
              "new_native_observations": 0, "heldout_credit": 0, "corpus_credit": 0, **reports[0]}
    with args.receipt.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
