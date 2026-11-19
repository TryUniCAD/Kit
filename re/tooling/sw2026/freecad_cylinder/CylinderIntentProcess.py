from argparse import ArgumentParser
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys


def main():
    parser = ArgumentParser(description="Inspect actual strict FreeCAD cylinders without constructing a native file")
    parser.add_argument("source_root", type=Path)
    parser.add_argument("mode", choices=("intent", "read", "public-refusal", "preparation-refusal"))
    parser.add_argument("--neutral-output", type=Path)
    parser.add_argument("--radius-edit-factor", type=float)
    parser.add_argument("--depth-edit-factor", type=float)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root.resolve(strict=True) / "src"))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from convert import open_document, write_document
    from convert.adapters.registry.RegistryErrors import AdapterNotFoundError
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from interchange.document.Models.DocumentModel import CadDocument
    from interchange.serialization.JsonCodec import LoadJson, DumpJson
    from CylinderSourceIntent import project, fingerprint, predict

    raw = sys.stdin.buffer.read()
    result = {"schema": "kit.sw2026.freecad-cylinder-intent-process.v1", "mode": args.mode,
              "passed": False, "input_sha256": sha256(raw).hexdigest(), "native_processes_started": 0,
              "heldout_inputs_read": 0, "generated_writer_outputs": 0}
    events = []
    code_reads = []

    def boundary(name, values):
        if name == "open" or name in ("subprocess.Popen", "os.system", "os.exec", "socket.connect"):
            if name == "open" and isinstance(values[0], (str, bytes)):
                path = Path(values[0].decode() if isinstance(values[0], bytes) else values[0])
                if path.suffix in (".py", ".pyc") and path.is_relative_to(args.source_root / "src"):
                    code_reads.append(str(path.relative_to(args.source_root)))
                    return
            events.append(name)
            raise RuntimeError(f"source-only projection crossed its process boundary: {name} {str(values[0])[:200]}")

    output = BytesIO()
    try:
        if args.mode == "read":
            document = open_document(raw, source_format="freecad.fcstd", include_brep=True, strict=True)
            if args.neutral_output is not None:
                with args.neutral_output.open("xb") as stream:
                    stream.write(DumpJson(document).encode())
            sys.addaudithook(boundary)
            result["intent"] = project(document)
            if args.radius_edit_factor is not None and args.depth_edit_factor is not None:
                result["prediction"] = predict(result["intent"], args.radius_edit_factor, args.depth_edit_factor)
                result["prediction_sha256"] = fingerprint(result["prediction"])
            result["source_projection_json_writes"] = int(args.neutral_output is not None)
            result["passed"] = True
        else:
            request = json.loads(raw)
            document = LoadJson(json.dumps(request["document"]))
            if type(document) is not CadDocument:
                raise ValueError("the source process requires a real CadDocument")
            sys.addaudithook(boundary)
            if args.mode == "intent":
                intent = project(document)
                result["intent"] = intent
                result["prediction"] = predict(intent, request["radius_edit_factor"], request["depth_edit_factor"])
                result["prediction_sha256"] = fingerprint(result["prediction"])
                result["passed"] = True
            elif args.mode == "preparation-refusal":
                try:
                    PrepareNative(document, r"C:\KitGenerated\Cylinder.SLDPRT", request["written_at"])
                except (TypeError, ValueError) as error:
                    result["refusal"] = {"type": type(error).__name__, "reason": str(error)}
                    result["passed"] = True
                else:
                    raise ValueError("the existing native preparer unexpectedly admitted the unprojected source")
            else:
                try:
                    write_document(document, output, destination_format="solidworks.sldprt", allow_carrier=False)
                except AdapterNotFoundError as error:
                    result["refusal"] = {"type": type(error).__name__, "reason": str(error)}
                    result["passed"] = output.getvalue() == b""
                else:
                    raise ValueError("the public writer unexpectedly admitted the unprojected source")
        result["native_bytes_emitted"] = len(output.getvalue())
        result["boundary_events"] = events
        result["code_import_reads"] = code_reads
    except Exception as error:
        result.update(error={"type": type(error).__name__, "reason": str(error)}, boundary_events=events,
                      code_import_reads=code_reads, native_bytes_emitted=len(output.getvalue()))
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    sys.exit(main())
