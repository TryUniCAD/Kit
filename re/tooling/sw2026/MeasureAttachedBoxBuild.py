from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from VerifyAttachedBoxSource import DISCLOSED, load_disclosed, require
from convert import write_document
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Preparation.FreecadBox.MakeOriginBoxPart import MakeOriginBoxPart
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxSource import ReadBoxSource
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit


ACCEPTED = ROOT / "re/solidworks/measurements/2026/AttachedTopBoxGeneratedNative01.json"
DESTINATIONS = {
    "0.21.2": "b200a6bbb1a206d5e5b188b880c8bb11948866bcfe731e8e248a31547489b5a6",
    "1.0.2": "96d878c67115f986217a84cd4c6e1219b41a8aec8c79dc505160470500419558",
    "1.1.4": "8e941aadf0fb430746de0b8bb9fca8f11941290d50749aeafbb99b08a59b361c",
}
MISSING_CAPABILITIES = ["brep", "native_payloads", "provenance", "roundtrip_metadata"]


def run(neutral, measured_requests):
    disclosed = load_disclosed(neutral)
    native_evidence = ACCEPTED.read_bytes()
    accepted = json.loads(native_evidence)
    inputs = {}
    for release, (document, source_model) in disclosed.items():
        name = f"recipe-{release}-F14c"
        raw = (measured_requests / name / "NeutralRequest.json").read_bytes()
        actual = json.loads(raw)
        prior = accepted["cases"][name]
        require(sha256(raw).hexdigest() == DESTINATIONS[release] and actual["document"] == source_model
                and actual["attached_top"] is True and actual["preserve_source_labels"] is True
                and document.source.sha256 == prior["input_sha256"] == DISCLOSED[release][1],
                "source or destination differs from native evidence")
        inputs[release] = (document, actual["native_path"], prior)

    codes = tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    require(all(codes), "runtime codecs unavailable")
    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    audit.BeginBuild()
    active = True

    def guard(event, args):
        if active:
            audit.InspectEvent(event, args)
            if event.startswith("socket.") or event == "ctypes.dlopen":
                raise PermissionError(f"attached box construction attempted {event}")

    sys.addaudithook(guard)
    outputs = {}
    try:
        for release, (original, destination, prior) in inputs.items():
            rows = {}
            for profile, document in (
                ("original", original),
                ("without_shape_cache", replace(original, brep=None, brep_payloads=())),
            ):
                translated = ReadBoxSource(document)
                part = MakeOriginBoxPart(
                    translated.ModelValue, destination, translated.CreationEpoch,
                    translated.PropertiesValue, UnitsValue=translated.UnitsValue, TopAttached=True,
                )
                digest = sha256(part.BytesValue).hexdigest()
                streams = {name: {"bytes": len(data), "sha256": sha256(data).hexdigest()}
                           for name, data in part.StreamsValue.items()}
                require(digest == prior["output_sha256"] and streams == prior["streams"],
                        "constructed candidate differs from the native-measured candidate")
                rows[profile] = {"candidate_sha256": digest, "candidate_bytes": len(part.BytesValue),
                                 "exact_streams": len(streams),
                                 "cache_compared": translated.GeometryValue["source_cache_compared"]}
            outputs[release] = {"source_sha256": original.source.sha256, "constructions": rows}
    finally:
        active = False

    require(not audit.DeniedReads, "part construction attempted a runtime read")
    for release, (document, _, _) in inputs.items():
        writer = SldprtWriter()
        missing = sorted(cap.value for cap in GetDocumentCaps(document) - writer.info.Capabilities)
        require(missing == MISSING_CAPABILITIES, "the public capability gap has changed")
        destination = BytesIO()
        require(not writer.supports(document, destination), "the public writer now admits this source")
        try:
            write_document(document, destination, destination_format=KPartFormatId, allow_carrier=False)
        except NotFoundError as error:
            require("does not support the destination" in str(error) and not destination.getvalue(),
                    "the registry did not refuse before any output")
            refusal = type(error).__name__
        else:
            raise ValueError("the public writer unexpectedly accepted the complete source")
        outputs[release]["public_writer"] = {"unsupported_capabilities": missing,
                                             "refusal": refusal,
                                             "published_bytes": len(destination.getvalue())}
    return {"schema": "kit.sw2026.attached-box-shared-construction.v1",
            "native_baseline_sha256": sha256(native_evidence).hexdigest(),
            "native_baseline_writer_revision": accepted["writer_revision"],
            "comparisons": outputs, "exact_part_comparisons": 6, "exact_stream_comparisons": 72,
            "runtime_input_file_reads": len(audit.DeniedReads), "retained_artifacts": 0,
            "new_native_runs": 0, "heldout_candidates_measured": 0, "public_writer_qualified": False}


if __name__ == "__main__":
    parser = ArgumentParser(description="Compare guarded shared box construction with the exact previously measured output")
    parser.add_argument("disclosed_neutral", type=Path)
    parser.add_argument("native_measured_requests", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.disclosed_neutral, args.native_measured_requests), indent=2, sort_keys=True, allow_nan=False))
