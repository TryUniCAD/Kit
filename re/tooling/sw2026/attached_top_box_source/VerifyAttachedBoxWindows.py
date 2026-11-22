from argparse import ArgumentParser
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from platform import machine, system
from subprocess import run
import sys
from zlib import ZLIB_RUNTIME_VERSION


SOURCE_SHA = "25c836424406343439bd3fa9acd82f8e6dbabdae689fe2a799099bf73805aafb"
MEASUREMENT_SHA = "35799ebe49e0b7a39673b65c3ef701577492c02d2df48c95706678bcc29062cd"
OUTPUT_SHA = "0d4cba0b66e443e487793204dc82985d5206704a0646b63afb1a4c410b1c54cc"
FORMAT = "solidworks.sldprt"
NATIVE_CAPS = {"body_structure", "brep", "configurations", "parameters", "parametric_history", "support_planes"}
EVIDENCE_CAPS = {"native_payloads", "provenance", "roundtrip_metadata"}
BOOTSTRAP = "import runpy,sys;sys.path.insert(0,sys.argv.pop(1));runpy.run_module('convert',run_name='__main__')"


def demand(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(raw):
    return sha256(raw).hexdigest()


def checked(path, expected):
    raw = path.read_bytes()
    demand(digest(raw) == expected, f"wrong content for {path.name}")
    return raw


def check_report(report):
    evidence = report["source_evidence"]
    transfers = report["transfers"]
    demand(report["vendor_loadable"] and report["application_usable"] and
           {item["capability"] for item in transfers} == NATIVE_CAPS and
           all(item["mode"] == "native" for item in transfers) and not report["dropped"],
           "publication omitted native CAD semantics")
    demand(evidence["source_sha256"] == SOURCE_SHA and
           set(evidence["evidence_only_capabilities"]) == EVIDENCE_CAPS and
           evidence["source_native_byte_replay"] is False, "publication omitted source evidence")
    return {"native_capabilities": sorted(NATIVE_CAPS), "source_evidence_capabilities": sorted(EVIDENCE_CAPS)}


def main():
    parser = ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("measurement", type=Path)
    parser.add_argument("sdk_src", type=Path)
    parser.add_argument("--trial", type=Path)
    args = parser.parse_args()
    demand(system() == "Windows", "physical publication requires Windows")
    sys.path.insert(0, str(args.sdk_src.resolve(strict=True)))
    from convert import open_document, write_document
    from convert.Commands.WriteReport import WriteReport

    source = open_document(checked(args.source, SOURCE_SHA), source_format="freecad.fcstd", strict=True)
    measurement = json.loads(checked(args.measurement, MEASUREMENT_SHA))
    native = json.loads(measurement["receipt"]["summary"])
    target = Path(native["candidate"]["native_path"])
    demand(target == Path(r"C:\KitAttachedBoxAxes01\F14c.SLDPRT"), "physical custody path differs")
    values = {"require_native_transfers": True, "solidworks_native_measurement": measurement}
    sink = BytesIO()
    preflight = write_document(source, sink, destination_format=FORMAT, allow_carrier=False,
                               values={**values, "final_destination": str(target)})
    demand(digest(sink.getvalue()) == OUTPUT_SHA, "Windows preflight has a different archive")
    result = {"schema": "kit.sw2026.attached-box-windows-publication.v1", "source_sha256": SOURCE_SHA,
              "archive_sha256": OUTPUT_SHA, "native_path": str(target), "python_version": sys.version.split()[0],
              "python_machine": machine(), "zlib_runtime": ZLIB_RUNTIME_VERSION,
              "pinned_oracle_build": native["oracle_build"],
              "stream_preflight": check_report(WriteReport(preflight)), "publications": []}
    if args.trial is None:
        print(json.dumps(result, sort_keys=True))
        return

    trial = args.trial.resolve()
    demand(trial.parent == target.parent and not trial.exists(), "trial requires a new native sibling directory")
    _ = checked(target, OUTPUT_SHA)
    trial.mkdir()
    locked = trial / "OriginalLocked.SLDPRT"
    target.rename(locked)
    try:
        for route in ("sdk_explicit", "sdk_inferred", "cli_explicit", "cli_inferred"):
            explicit = route.endswith("_explicit")
            if route.startswith("sdk_"):
                options = {"destination_format": FORMAT} if explicit else {}
                report = WriteReport(write_document(source, target, allow_carrier=False, values=values, **options))
            else:
                flags = ("--to", FORMAT) if explicit else ()
                outcome = run((sys.executable, "-I", "-B", "-c", BOOTSTRAP, str(args.sdk_src),
                               "convert", str(args.source), str(target), *flags, "--native-measurement",
                               str(args.measurement), "--json"), capture_output=True, text=True, timeout=120)
                demand(outcome.returncode == 0 and not outcome.stderr, outcome.stderr or outcome.stdout)
                report = json.loads(outcome.stdout)
            raw = checked(target, OUTPUT_SHA)
            result["publications"].append({"route": route, "bytes": len(raw), **check_report(report)})
            target.rename(trial / (route + ".SLDPRT"))
    finally:
        if target.exists():
            target.rename(trial / "InterruptedOutput.SLDPRT")
        locked.rename(target)
    _ = checked(target, OUTPUT_SHA)
    demand(len(result["publications"]) == 4, "publication trials are incomplete")
    result["original_restored"] = True
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
