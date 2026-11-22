from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from pathlib import Path, PureWindowsPath
from subprocess import run
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent), str(HERE.parent / "sweep_source")]

from CheckScopedPlainWriter import WriterAudit
from SweepSdkInput import neutral_document
from convert.adapters.registry import AdapterNotFoundError

FORMAT = "solidworks.sldprt"
OPTION = "solidworks_native_measurement"
NATIVE_SHA = "380ead8ff07a9337bd0df87d32eb92e49529e0579c15449767a5ee26e53dd512"
RECEIPT = ROOT / "re/solidworks/measurements/2026/SdkStandardSweepReceipt01.json"
RECEIPT_SHA = "fc098693d77e0e41e5652eed80fe705b528db9cb9f6ac527fb379784087d83d0"
SPEC = HERE.parent / "sweep_source/DisclosedSweepInputs.json"
SPEC_SHA = "e62d1d09ac26cc0ae9538a846b0800023441403b5d04ac432a8f6b1da8e71023"


def require(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


def digest(value):
    return sha256(value).hexdigest()


def pinned(path, expected):
    value = path.read_bytes()
    require(digest(value) == expected, f"wrong disclosed evidence digest for {path.name}")
    return value


def reject(action, sink=None, diagnostic=None):
    try:
        action()
    except (AdapterNotFoundError, OSError, TypeError, ValueError) as error:
        require(diagnostic is None or diagnostic in str(error), str(error))
    else:
        raise ValueError("unqualified request reached output")
    if sink is not None:
        require(sink.getvalue() == b"unchanged" and sink.tell() == 0, "refusal mutated the output stream")


def intentionally_bad(job, document, options):
    step, = document.feature_timeline
    section, _ = document.sketches
    wrong_path = replace(step.definition, PathSketchId=section.id)
    bad_mass = deepcopy(options)
    states = bad_mass[OPTION]["receipt"]["cases"][job["slot"]]["states"]
    states[1]["volume_m3"] *= 1.0000004
    states[2]["volume_m3"] *= 1.0000008
    bad_area = deepcopy(options)
    bad_area[OPTION]["receipt"]["cases"][job["slot"]]["states"][0]["area_m2"] *= 1.001
    bad_center = deepcopy(options)
    bad_center[OPTION]["receipt"]["cases"][job["slot"]]["states"][3]["com_m"][0] *= 1.001
    return (
        ("crossed_owner", replace(document, feature_timeline=(replace(step, definition=wrong_path),)), options, None),
        ("untransferred_domain", replace(document, metadata=dict(document.metadata, extra=True)), options, None),
        ("unmeasured_model", neutral_document(job["name"], job["edit_section"], job["path"], job["density"]), options,
         "no unique exact native measurement"),
        ("absent_receipt", document, {key: value for key, value in options.items() if key != OPTION},
         "requires an offline native measurement receipt"),
        ("shifted_locator", document, dict(options, final_destination=rf"C:\Different\{job['name']}.SLDPRT"),
         "no unique exact native measurement"),
        ("reopened_volume", document, bad_mass, "disagrees with quarter tube geometry"),
        ("initial_area", document, bad_area, "disagrees with quarter tube geometry"),
        ("edited_center", document, bad_center, "disagrees with quarter tube geometry"),
    )


def project_writes(job, folder):
    from convert import open_document, write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.base.WritePolicy import GetDocumentCaps
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.Preparation.Sweeps.PrepSweepPart import PrepSweepPart
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
    from interchange.document.Models.DocumentModel import CadDocument

    for codec in ("utf-8", "utf-16-le", "ascii", "latin-1", "cp1252"):
        lookup(codec)
    for module in ("interchange.document.Models.DocumentProvenance", "interchange.brep.Validation.BrepValidate",
                   "interchange.document.Behavior.DocumentIo", "interchange.document.Validation.DocumentAssemblyValidate",
                   "interchange.document.Validation.DocumentFeatureValidate", "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    authored = neutral_document(job["name"], job["section"], job["path"], job["density"])
    source = authored.to_json(indent=None)
    document = CadDocument.from_json(source)
    require(document == authored and document.to_json(indent=None) == source, "portable JSON altered typed source ownership")
    locator = job["locator"]
    folder = Path(folder)
    target = folder / PureWindowsPath(locator).name
    audit = WriterAudit(ROOT / "src", target)
    sys.addaudithook(audit.observe)
    options = {"final_destination": locator, OPTION: job["measurement"], "require_native_transfers": True}

    def transfer(model, sink, values, direct):
        if direct:
            return SldprtWriter().write(model, sink, WriteOptions(values=values))
        return write_document(model, sink, destination_format=FORMAT, allow_carrier=False, values=values)

    audit.phase = "write"
    rejected = []
    for name, model, values, diagnostic in intentionally_bad(job, document, options):
        for direct in (False, True):
            sink = BytesIO(b"unchanged")
            reject(lambda: transfer(model, sink, values, direct), sink, diagnostic)
        rejected.append(name)
    for direct in (False, True):
        sink = BytesIO(b"unchanged")
        reject(lambda: transfer(document, sink, options, direct), sink)
        reject(lambda: transfer(document, target, options, direct))
    candidate = PrepSweepPart(document, BytesIO(), job["measurement"]["written_at"], WriteOptions(values=options))
    sinks = (BytesIO(), BytesIO())
    outcome = tuple(transfer(document, sink, options, direct) for direct, sink in enumerate(sinks))
    audit.phase = "done"
    require(not target.exists() and not tuple(folder.iterdir()), "failed filesystem route left output or staging")
    payload = candidate.BytesValue
    require(digest(payload) == job["sha256"] and len(payload) == job["bytes"]
            and all(sink.getvalue() == payload for sink in sinks), "normal SDK output changed measured bytes")
    flags = [(row.vendor_loadable, row.application_usable, row.dropped, row.native_capabilities) for row in outcome]
    caps = GetDocumentCaps(document)
    require(len(caps) == 6 and all(loadable and usable and not dropped and native == caps for loadable, usable, dropped, native in flags),
            f"incomplete transfer or qualification: {flags}; source {caps}")
    require(not audit.denied and audit.target_opens == 0, "output path touched storage before attestation")
    parsed = SldprtArchive.from_bytes(payload)
    stream_hashes = {name: digest(data) for name, data in sorted(parsed.streams.items())}
    require(len(stream_hashes) == 11 and parsed.streams == candidate.StreamsValue
            and (job["streams"] is None or stream_hashes == job["streams"]), "physical stream identity drifted")
    reopened = open_document(payload)
    reader_status = {"body_geometry": reopened.brep is not None, "feature_count": len(reopened.feature_timeline),
                     "sketch_count": len(reopened.sketches),
                     "has_portable_sweep": any(type(step.definition).__name__ == "SweepFeature" for step in reopened.feature_timeline),
                     "diagnostics": [row.message for row in reopened.diagnostics]}
    try:
        ReadNativeLink(parsed, 0)
    except ValueError as error:
        reader_status["typed_refusal"] = str(error)
    else:
        reader_status["typed_refusal"] = None
    return {"name": job["name"], "archive_sha256": job["sha256"], "archive_bytes": len(payload),
            "stream_sha256": stream_hashes, "normalized_state_checks": 30,
            "exact_registry_and_direct_streams": True, "native_transfers": len(caps),
            "fresh_attempt_refusals": rejected, "occupied_stream_and_unverified_path_refused": True,
            "writer_runtime_input_reads": len(audit.denied), "sdk_readback": reader_status}


def supervise(native=None):
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    spec = json.loads(pinned(SPEC, SPEC_SHA))
    receipt = json.loads(pinned(RECEIPT, RECEIPT_SHA))
    require(receipt["native_result_sha256"] == NATIVE_SHA, "normalized provenance changed")
    if native is not None:
        pinned(native / "DisclosedRecords/Result.json", NATIVE_SHA)
    results = []
    for case, row in zip(spec["cases"], receipt["cases"], strict=True):
        locator = row["locator"]
        name = case["name"]
        require(name == PureWindowsPath(locator).stem, "authored and recorded case differ")
        expected_streams = None
        if native is not None:
            data = pinned(native / "Packet/Candidates" / PureWindowsPath(locator).name, row["archive_sha256"])
            archive = SldprtArchive.from_bytes(data)
            expected_streams = {path: digest(value) for path, value in archive.streams.items()}
        job = {"name": name, "slot": row["slot"], "locator": locator, "sha256": row["archive_sha256"],
               "bytes": row["archive_bytes"], "streams": expected_streams, "density": spec["density_kg_m3"],
               "section": case["section_radius_m"], "path": case["path_radius_m"], "edit_section": case["edit_section_radius_m"],
               "measurement": {"written_at": row["written_at"], "receipt": receipt}}
        with TemporaryDirectory(prefix="KitScopedSweep") as folder:
            worker = run((sys.executable, "-I", "-B", str(HERE), "--worker", folder),
                         input=json.dumps(job), capture_output=True, text=True, timeout=45, check=False)
            require(worker.returncode == 0, worker.stderr or worker.stdout)
        results.append(json.loads(worker.stdout))
    return {"schema": "kit.sw2026.main-scoped-sweep.v1", "base": "e5294382aad0c04ba26554dfe381fd03daec110a",
            "native_result_sha256": NATIVE_SHA, "normalized_receipt_sha256": RECEIPT_SHA, "neutral_spec_sha256": SPEC_SHA,
            "writer_processes": len(results), "native_calls": 0, "protected_inputs_read": 0,
            "disclosed_physical_stream_comparison": native is not None, "cases": results}


if __name__ == "__main__":
    parser = ArgumentParser(description="Reproduce the two disclosed measured sweep writes without an oracle")
    parser.add_argument("--native", type=Path, help="optional original disclosed capture directory")
    parser.add_argument("--worker")
    args = parser.parse_args()
    result = project_writes(json.load(sys.stdin), args.worker) if args.worker else supervise(args.native)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
