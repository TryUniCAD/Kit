import argparse
import codecs
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sdk", type=Path, required=True)
    parser.add_argument("--fault", required=True)
    args = parser.parse_args()
    row = json.loads(sys.stdin.read())
    sys.path[:0] = [str(args.sdk / "src"), str(Path(__file__).resolve().parent)]
    from convert import open_document
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
    from BuildChronology01 import compose
    from ChronologyFaults01 import rejected
    from MakeRevolveRequest01 import make_request
    for encoding in ("ascii", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "latin-1"):
        codecs.lookup(encoding)
    for name in ("interchange.document.Behavior.DocumentIo", "interchange.brep.Validation.BrepValidate", "interchange.document.Models.DocumentProvenance", "interchange.document.Validation.AngleRevValidate", "interchange.document.Validation.DocumentAssemblyValidate", "interchange.document.Validation.DocumentFeatureValidate", "interchange.document.Validation.DocumentReferenceValidate", "interchange.document.Validation.PlaneRevValidate", "interchange.document.Validation.DistExtValidate"):
        import_module(name)
    state = {"enabled": False, "attempts": []}

    def audit(event, arguments):
        if state["enabled"] and (event == "open" or event.startswith(("subprocess.", "socket.")) or event in ("os.system", "os.fork", "os.posix_spawn", "ctypes.dlopen")):
            state["attempts"].append(event)
            raise RuntimeError("rejected chronology attempted external runtime access")

    sys.addaudithook(audit)
    state["enabled"] = True
    result = {"schema": "kit.sw2026.part-chronology-rejected-process.v1", "passed": False, "fault": args.fault, "heldout_inputs_read": 0, "native_processes": 0}
    try:
        document, settings = make_request(row["spec"])
        candidate = compose(document, settings, "coupled")
        require(sha256(candidate["bytes"]).hexdigest() == row["sha256"], "negative process prerequisite changed the original candidate")
        loaded = open_document(candidate["bytes"], source_format="solidworks.sldprt", strict=True)
        loaded.assert_valid()
        require(loaded.brep is not None and not loaded.brep.validate(frozenset(body.id for body in loaded.bodies)), "negative prerequisite did not produce validated strict geometry")
        counter = candidate["allocator"].NextValue
        expected_error = TypeError if args.fault == "unnamed_owner" else ValueError
        try:
            rejected(candidate, args.fault)
        except expected_error as error:
            diagnostic = str(error)
            diagnostic_class = type(error).__name__
        else:
            raise AssertionError("invalid chronology reached header construction")
        require(candidate["allocator"].NextValue == counter, "rejection advanced actual persistent allocation")
        config_bytes, config = WriteConfigMut(candidate["system"].RootValue, 19000, candidate["headers"][0])
        roots = (*candidate["system"].FeatureValues, candidate["profile"].ProfileValue, candidate["feature"])
        resolved_bytes, resolved = WriteResolMut(roots, None, 19000, config.MapValue, candidate["resolved"].ContextValue)
        require(config_bytes == candidate["streams"]["Contents/Config-0"] and resolved_bytes == candidate["streams"]["Contents/Config-0-ResolvedFeatures"], "rejection changed actual model topology or native reference state")
        require(WriteHeadGraph(candidate["headers"][0], 19000) == candidate["streams"]["Contents/Config-0-ModelHeader"] and WriteHeadGraph(candidate["headers"][1], 19000) == candidate["streams"]["Header2"], "rejection mutated an existing header role")
        result.update(passed=True, diagnostic=diagnostic, diagnostic_class=diagnostic_class, prerequisite_generated_sha256=row["sha256"], complete_sdk_prerequisite_read=True, allocator_unchanged=True, config_resolved_headers_unchanged=True)
    finally:
        state["enabled"] = False
    result["runtime_external_attempts"] = state["attempts"]
    result["sdk_modules"] = sorted({module.__file__ for name, module in sys.modules.items() if (name == "convert" or name.startswith(("convert.", "interchange."))) and getattr(module, "__file__", None)})
    print(json.dumps(result, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
