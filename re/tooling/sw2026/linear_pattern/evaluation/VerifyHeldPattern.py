from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from pathlib import Path
from subprocess import run
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent / "default_parity"),
                str(HERE.parent / "public_parity")]

from PatternParityPacket import PRIOR_RESULT, SOURCE_TRIAL, checked, encode, require, verified_packet
from RunPatternDefaultParity import old_tools

MEASURE = "solidworks_native_measurement"
FORMAT = "solidworks.sldprt"
DEFAULT_NATIVE = "f6066ca8a258b2394744632d3062dfdf02bdda3207b84467555f27a0a8a53197"
PARITY = "cb2d03309afd69b3db52a620433f7a828a4a81618574fe6b5d73ad2a93f169fc"
PUBLIC_PARITY = "f9580031c92d3ac6ca97ee905ab161bf5e6c8a3dd3849f6e61fe14ce7bfa53e3"


def worker(job):
    from PublicPatternWorker import check_result, require_strict
    from LocalPatternContainerProcess import audit, linked
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
    from convert.adapters.solidworks.Core.Preparation.Patterns.PrepPatPart import PrepPatPart
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
    from interchange import CadDocument

    for module in ("interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo",
                   "interchange.document.Models.DocumentProvenance", "interchange.document.Validation.DocumentValidate",
                   "interchange.document.Validation.DocumentAssemblyValidate",
                   "interchange.document.Validation.DocumentFeatureValidate",
                   "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    for codec in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        lookup(codec)
    request = job["request"]
    target = request["target"]
    raw = encode(request["document"]).decode()
    model = CadDocument.from_json(raw)
    restored = CadDocument.from_json(model.to_json())
    require(model == restored, "portable pattern changed after neutral JSON")
    expected = job["expected"]
    locator = Path(target["PathName"])
    native = {"written_at": target["SavedAt"], "receipt": {"native_report": job["report"]}}
    values = {"final_destination": str(locator), MEASURE: native}
    invalid = {
        "crossed_receipt": (values | {MEASURE: {**native, "receipt": {"native_report": job["other"]}}},
                            "no exact held-out native measurement"),
        "edited_receipt": (values | {MEASURE: {**native, "receipt": {"native_report": job["report"] | {
            "source_lock_sha256": expected["generated_sha256"]}}}},
                           "authenticated held-out evidence"),
        "wrong_epoch": (values | {MEASURE: native | {"written_at": native["written_at"] + 1}},
                        "no exact held-out native measurement"),
        "wrong_locator": (values | {"final_destination": str(locator.parent / "Other" / locator.name)},
                          "no exact held-out native measurement"),
        "missing_receipt": ({"final_destination": str(locator)}, "offline native measurement receipt"),
    }

    def registry(document, sink, options):
        return write_document(document, sink, destination_format=FORMAT, allow_carrier=False, values=options)

    def direct(document, sink, options):
        return SldprtWriter().write(document, sink, WriteOptions(values=options))

    def adapter(document, sink, options):
        return SldprtAdapter().write(document, sink, WriteOptions(values=options))

    audit.BeginBuild()
    routes = {}
    for call in (registry, direct, adapter):
        for document in (model, restored):
            sink = BytesIO()
            result = call(document, sink, values)
            payload = sink.getvalue()
            check_result(result, payload)
            metadata = result.metadata[MEASURE]
            require(sha256(payload).hexdigest() == expected["generated_sha256"] and len(payload) == expected["bytes"]
                    and metadata["qualified_slot"] == expected["slot"]
                    and metadata["authority_sha256"] == job["authority"], "generated pattern differs from its measured archive")
        for changes, message in invalid.values():
            sink = BytesIO(b"preserve binary destination")
            sink.seek(5)
            try:
                call(model, sink, changes)
            except ValueError as refusal:
                require(message in str(refusal), "pattern refused at the wrong boundary")
            else:
                raise ValueError("unqualified pattern was published")
            require(sink.getvalue() == b"preserve binary destination" and sink.tell() == 5,
                    "refused pattern changed its sink")
        routes[call.__name__] = {"archives": 2, "refusals": list(invalid)}

    archive = SldprtArchive.from_bytes(payload)
    baseline = PrepPatPart(model, BytesIO(), target["SavedAt"],
                           WriteOptions(values={"final_destination": str(locator)})).BytesValue
    prior_streams = SldprtArchive.from_bytes(baseline).streams
    view_changes = sorted(name for name in archive.streams if archive.streams[name] != prior_streams[name])
    require(archive.streams.keys() == prior_streams.keys() and view_changes == ["Contents/Config-0"],
            "the earlier platform calculation changed a stream outside the standard view owner")
    link, headers = linked(payload, archive.streams)
    require(len(archive.streams) == 10 and len(link.ResolvedValue.RootsValue) == 24 and len(headers) == 2,
            "generated pattern has a different owner inventory")
    require_strict(payload, model, model.configurations[0].name)
    require(not audit.DeniedReads and not {"pythoncom", "win32com", "Swapp"}.intersection(sys.modules),
            "protected pattern writer accessed inputs or CAD")
    return {"slot": expected["slot"], "archive_sha256": expected["generated_sha256"], "bytes": len(payload),
            "stream_count": len(archive.streams), "typed_stream_replays": 9, "strict_read": True,
            "publication_routes": routes, "runtime_input_reads": len(audit.DeniedReads),
            "alternate_view_stream_changes": view_changes}


def child(path, mode, request):
    outcome = run((sys.executable, "-I", "-B", str(path), mode), input=encode(request), capture_output=True,
                  check=False, timeout=90)
    require(outcome.returncode == 0 and not outcome.stderr, "isolated " + mode + " process refused")
    return json.loads(outcome.stdout)


def supervise(share):
    require(sys.platform == "win32" and sys.version_info[:2] == (3, 12), "protected model requires Windows Python 3.12")
    packet = share / "LinearPatternDefaultParity01" / "Packet"
    manifest = verified_packet(packet, PARITY)
    reports = ROOT / "re/solidworks/measurements/2026"
    prior = json.loads(checked(reports / "LocalLinearPatternDatumHeldoutNative01.json", PRIOR_RESULT))
    default = json.loads(checked(reports / "LocalLinearPatternDefaultNative01.json", DEFAULT_NATIVE))
    evidence = json.loads(checked(reports / "LocalLinearPatternPublicParity01.json", PUBLIC_PARITY))
    _, old_source, plan, guard, angle, epoch = old_tools(packet)
    lock, frozen = old_source.source_freeze(share / SOURCE_TRIAL)
    require(manifest["prior_result_sha256"] == PRIOR_RESULT and prior["source_lock_sha256"] == old_source.SOURCE_SHA
            and lock["passed"] and default["source_lock_sha256"] == evidence["source_lock_sha256"] == old_source.SOURCE_SHA,
            "the retained neutral intent and native reports have different source locks")
    home = Path(old_source.PRIVATE_EVAL)
    rows = []
    bridge = HERE.parent / "default_parity/PatternDefaultWorker.py"
    for source, expected, report, other, authority in zip(frozen["cases"], evidence["cases"], (prior, default),
                                                          (default, prior), (PRIOR_RESULT, DEFAULT_NATIVE), strict=True):
        slot = source["slot"]
        qualified = prior["cases"][0] if slot == "Slot01" else default
        require(slot == expected["slot"] == qualified["slot"] and qualified["passed"]
                and expected["generated_sha256"] == qualified["generated_sha256"],
                "protected source slot does not match its native-qualified artifact")
        locator = home / "Native" / slot / "Candidates" / source["filenames"]["original"]
        guard(locator, home)
        request = child(bridge, "--bridge", plan(source, locator, epoch, angle)["original"]["modeled_input"])
        rows.append(child(HERE, "--worker", {"request": request, "expected": expected, "report": report,
                                             "other": other, "authority": authority}))
    return {"schema": "kit.sw2026.heldout-linear-pattern-publication.v1", "cases": rows,
            "guarded_workers": len(rows), "native_processes_started": 0, "original_native_sources_read": 0,
            "authority_sha256": [PRIOR_RESULT, DEFAULT_NATIVE], "source_lock_sha256": old_source.SOURCE_SHA}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--share", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    result = worker(json.load(sys.stdin)) if args.worker else supervise(args.share)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
