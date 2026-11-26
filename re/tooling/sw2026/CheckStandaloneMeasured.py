from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
from CheckMeasuredPartWriter import OPTION, FORMAT, check_custody, demand, read_pinned
from CheckScopedPlainWriter import WriterAudit, reject


class NonSeekSink:
    def __init__(self):
        self.data = b""

    def write(self, data):
        self.data += data
        return len(data)


def actual_sinks(root, request, directory):
    sys.path.insert(0, str(root / "src"))
    archive_path = request["expected_locator"]
    name = request["document"]["metadata"]["name"] + ".SLDPRT"
    audit = WriterAudit(root / "src", directory / name)
    first_path, second_path = directory / "registry.bin", directory / "direct.bin"
    with first_path.open("wb") as registry_file, second_path.open("wb") as direct_file:
        sys.addaudithook(audit.observe)
        from convert import open_document, write_document
        from convert.adapters.base.WriteOptions import WriteOptions
        from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
        from interchange.document.Models.DocumentModel import CadDocument

        for name in ("interchange.document.Behavior.DocumentIo",
                     "interchange.document.Models.DocumentProvenance",
                     "interchange.document.Validation.DocumentAssemblyValidate",
                     "interchange.document.Validation.DocumentFeatureValidate",
                     "interchange.document.Validation.DocumentReferenceValidate"):
            import_module(name)
        for codec in ("utf-8", "utf-16-le", "latin-1", "cp1252"):
            lookup(codec)
        doc = CadDocument.from_json(json.dumps(request["document"]))
        options = {"final_destination": archive_path, OPTION: request["evidence"]}
        writer = SldprtWriter()
        boundaries = {
            "registry": (lambda target: write_document(doc, target, destination_format=FORMAT,
                                                      allow_carrier=False, values=options), registry_file),
            "direct": (lambda target: writer.write(doc, target, WriteOptions(values=options)), direct_file),
        }
        verdicts = {}
        audit.phase = "write"
        for label, (publish, writable_file) in boundaries.items():
            demand(not writable_file.readable() and writable_file.seekable(),
                   "the file control must exercise a normal write-only sink")
            states = []
            for kind, original, cursor in (
                ("stale_tail", b"original suffix", 0),
                ("prefix", b"original prefix", len(b"original prefix")),
                ("displaced_empty_cursor", b"", 30),
            ):
                candidate = BytesIO(original)
                candidate.seek(cursor)
                reject(lambda: publish(candidate), ValueError, "empty seekable binary stream")
                demand(candidate.getvalue() == original and candidate.tell() == cursor,
                       "refusal changed the caller bytes or cursor")
                states.append(kind)
            unseekable = NonSeekSink()
            reject(lambda: publish(unseekable), ValueError, "empty seekable binary stream")
            demand(not unseekable.data, "unseekable caller received bytes")
            fresh = BytesIO()
            flags = [publish(target) for target in (fresh, writable_file)]
            data = fresh.getvalue()
            demand(all(item.vendor_loadable and item.application_usable and item.bytes_written == len(data)
                       for item in flags) and sha256(data).hexdigest() == request["expected_sha256"],
                   "standalone publication did not reproduce the native-tested digest")
            verdicts[label] = {"refusals": [*states, "nonseekable"], "accepted_sinks": 2,
                               "final_cursor": fresh.tell()}
        generic = BytesIO(b"keep existing prefix\n")
        generic.seek(len(generic.getvalue()))
        prefix_boundary = generic.tell()
        result = write_document(doc, generic, destination_format="interchange.json")
        demand(result.bytes_written == generic.tell() - prefix_boundary and
               generic.getvalue().startswith(b"keep existing prefix\n"),
               "generic writer lost its ordinary append behavior")
        audit.phase = "done"
    for path in (first_path, second_path):
        demand(sha256(path.read_bytes()).hexdigest() == request["expected_sha256"],
               "write-only file differs from exact measured bytes")
    demand(open_document(generic.getvalue()[prefix_boundary:], source_format="interchange.json") == doc,
           "generic append no longer preserves the neutral document")
    demand(not audit.denied and not audit.target_opens
           and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules),
           "standalone publication accessed a runtime input or CAD runtime")
    return {"case": request["role"], "archive_sha256": request["expected_sha256"], "boundaries": verdicts,
            "generic_append": True, "runtime_input_reads": 0}


def home_receipt(root, request):
    bootstrap = """import sys
sys.path.insert(0, sys.argv.pop(1))
from convert.Commands.MainEntry import MainEntry
raise SystemExit(MainEntry())
"""
    with TemporaryDirectory(prefix="KitTildeReceipt-", dir=root) as scratch:
        base = Path(scratch)
        source = base / "Neutral.json"
        target = base / (request["document"]["metadata"]["name"] + ".SLDPRT")
        evidence = base / "Measured.json"
        source.write_text(json.dumps(request["document"]), encoding="utf-8")
        evidence.write_text(json.dumps(request["evidence"]), encoding="utf-8")
        argument = "~/" + evidence.resolve().relative_to(Path.home().resolve()).as_posix()
        process = subprocess.run(
            [sys.executable, "-I", "-B", "-c", bootstrap, str(root / "src"), "convert",
             str(source), str(target), "--json", "--native-measurement", argument],
            capture_output=True, text=True, check=False, timeout=40,
        )
        demand(process.returncode == 0 and not process.stderr, process.stderr)
        report = json.loads(process.stdout)
        demand(report["application_usable"] and report["vendor_loadable"] and
               sha256(target.read_bytes()).hexdigest() == request["expected_sha256"],
               "literal tilde receipt did not reproduce the measured native file")
    return True


def supervise(root, native, output):
    receipt = json.loads((root / "re/solidworks/measurements/2026/SdkDefaultPartNative01.json").read_bytes())
    epoch = check_custody(native, receipt)
    entries = []
    for row in receipt["builds"]:
        role = row["role"]
        request = read_pinned(native / role / "SdkRequest.json", row["request_sha256"])
        demand(request["written_at"] == epoch, "native authoring epoch changed")
        request |= {"role": role, "expected_sha256": row["candidate_sha256"],
                    "evidence": {"written_at": epoch, "receipt": receipt}}
        check = subprocess.run(
            [sys.executable, "-I", "-B", str(HERE), "--root", str(root), "--worker"],
            input=json.dumps(request), capture_output=True, text=True, check=False, timeout=40,
        )
        demand(check.returncode == 0 and not check.stderr, check.stderr)
        entries.append(json.loads(check.stdout) | {"literal_tilde_receipt": home_receipt(root, request)})
    adapters = root / "src/convert/adapters"
    staging = adapters / "Staging"
    writing = adapters / "solidworks/Core/Writing"
    paths = [
        *(staging / f"{name}.py" for name in ("CheckWholeSink", "SeekBinary", "SinkExtentMut", "StreamStaging", "WriteWholeMut")),
        adapters / "base/WholeStreamWriter.py", writing / "EmitNativeMut.py", writing / "SldprtWriter.py",
        *(writing / "Measured").glob("*.py"), root / "src/convert/Commands/NativeMeasVals.py",
    ]
    result = {"schema": "kit.sw2026.standalone-measured-stream-proof.v1", "cases": entries,
              "native_result_sha256": receipt["native_result_sha256"], "native_launches": 0,
              "oracle_phases": receipt["distinct_native_processes"], "numeric_native_checks": receipt["numeric_checks"],
              "source_sha256": {path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
                                for path in sorted(paths)},
              "method_sha256": sha256(HERE.read_bytes()).hexdigest()}
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(sha256(output.read_bytes()).hexdigest())


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--native", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        with TemporaryDirectory(prefix="KitStandaloneStream-") as folder:
            print(json.dumps(actual_sinks(args.root, json.load(sys.stdin), Path(folder).resolve())))
    else:
        supervise(args.root, args.native, args.output)
