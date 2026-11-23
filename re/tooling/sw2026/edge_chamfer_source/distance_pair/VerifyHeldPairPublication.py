from argparse import ArgumentParser
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from subprocess import run
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from CheckMeasuredPair import warm_modules
from convert import write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.document.Models.DocumentModel import CadDocument

AUTHORITY = "00ebeab7479f9a9cc6468d4f91412e0a15bb162c65c4fdf32536d23b21857c36"
OPTION = "solidworks_native_measurement"
FORMAT = "solidworks.sldprt"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def pinned(path, expected):
    payload = path.read_bytes()
    require(digest(payload) == expected, "protected measurement input has changed")
    return json.loads(payload)


def registry(document, sink, options):
    return write_document(document, sink, destination_format=FORMAT, allow_carrier=False, values=options)


def adapter(document, sink, options):
    return SldprtAdapter().write(document, sink, WriteOptions(values=options))


def direct(document, sink, options):
    return SldprtWriter().write(document, sink, WriteOptions(values=options))


def refuse(call, document, options, expected):
    sink = BytesIO(b"preserve caller bytes")
    sink.seek(6)
    try:
        call(document, sink, options)
    except ValueError as failure:
        require(expected in str(failure), "request refused at the wrong boundary")
    else:
        raise ValueError("unqualified request published")
    require(sink.getvalue() == b"preserve caller bytes" and sink.tell() == 6,
            "refused output changed its sink")


def worker(job):
    warm_modules()
    source, report, expected = job["intent"], job["native"], job["generation"]
    document = CadDocument.from_json(json.dumps(source["document"]))
    epoch, locator = source["epoch"], source["locator"]
    options = {"final_destination": locator, OPTION: {"written_at": epoch, "receipt": {"native_report": report}}}
    attempted = []

    def access(event, _):
        if event in {"open", "os.listdir", "os.scandir", "os.exec", "os.posix_spawn", "os.system", "subprocess.Popen", "ctypes.dlopen"} or event.startswith("socket."):
            attempted.append(event)
            raise RuntimeError("guarded writer attempted external access: " + event)

    untrusted = deepcopy(report)
    untrusted["private_result_sha256"] = report["generation_sha256"]
    scenarios = {
        "unbound_report": (options | {OPTION: {"written_at": epoch, "receipt": {"native_report": untrusted}}},
                           "authenticated held-out evidence"),
        "wrong_epoch": (options | {OPTION: options[OPTION] | {"written_at": epoch + 1}},
                        "no unique exact held-out native measurement"),
        "wrong_locator": (options | {"final_destination": str(Path(locator).parent / "Foreign" / Path(locator).name)},
                          "no unique exact held-out native measurement"),
        "missing_receipt": ({"final_destination": locator}, "requires an offline native measurement receipt"),
    }
    sys.addaudithook(access)
    results = {}
    for call in (registry, adapter, direct):
        sink = BytesIO()
        result = call(document, sink, options)
        raw = sink.getvalue()
        evidence = result.metadata[OPTION]
        require(result.vendor_loadable and result.application_usable and result.bytes_written == len(raw)
                and digest(raw) == expected["archive_sha256"] and len(raw) == expected["archive_bytes"]
                and evidence["authority_sha256"] == AUTHORITY and evidence["native_result_sha256"] == report["private_result_sha256"]
                and len(evidence["phase_record_sha256"]) == 2, "protected public stream does not match measured output")
        archive = SldprtArchive.from_bytes(raw)
        require({name: digest(payload) for name, payload in archive.streams.items()} == expected["streams"],
                "protected public stream changed decoded streams")
        for changed, message in scenarios.values():
            refuse(call, document, changed, message)
        results[call.__name__] = {"stream_count": len(archive.streams), "refusals": list(scenarios)}
    require(not attempted and not any(module.startswith(("win32com", "pythoncom")) for module in sys.modules),
            "protected publication accessed an external file or CAD runtime")
    return {"slot": job["slot"], "archive_sha256": expected["archive_sha256"], "bytes": expected["archive_bytes"],
            "publication_routes": results, "runtime_input_file_reads": len(attempted)}


def supervise(packet):
    receipt_path = ROOT / "re/solidworks/measurements/2026/ChamferDistancePairHeldoutNative01.json"
    native = pinned(receipt_path, AUTHORITY)
    generated = pinned(packet / "Generated.json", native["generation_sha256"])
    _ = pinned(packet.parent / "Capture" / "Result.json", native["private_result_sha256"])
    require(generated["cohort"] == "heldout" and generated["writer_revision"] == native["writer_revision"],
            "the generation manifest does not belong to the locked cohort")
    results = []
    for index, (model, measured) in enumerate(zip(generated["candidates"], native["candidates"], strict=True)):
        intent = pinned(packet / f"Neutral{index}.json", model["neutral_sha256"])
        require(model["archive_sha256"] == measured["candidate_sha256"] and index == measured["slot"],
                "protected archive and native slot differ")
        job = {"slot": index, "intent": intent, "native": native, "generation": model}
        child = run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=json.dumps(job), text=True,
                    capture_output=True, check=False, timeout=120)
        require(child.returncode == 0 and not child.stderr, child.stderr)
        results.append(json.loads(child.stdout))
    require(len(results) == 2, "protected publication requires both independently locked candidates")
    return {"schema": "kit.sw2026.heldout-distance-pair-publication.v1", "cases": results, "guarded_workers": len(results),
            "native_processes_started": 0, "original_native_sources_read": 0,
            "existing_native_comparisons": sum(case["native_source_comparisons"] for case in native["candidates"]),
            "authority_sha256": AUTHORITY, "generation_sha256": native["generation_sha256"]}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--worker", action="store_true")
    options = parser.parse_args()
    result = worker(json.load(sys.stdin)) if options.worker else supervise(options.packet)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
