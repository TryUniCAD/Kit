from argparse import ArgumentParser
import codecs
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from pathlib import Path, PureWindowsPath
from subprocess import run
import sys

from BuildPrincipalRevolves import authored_neutral, measure


GENERATION = "30b127f6bd04746e79019180099f62e55b87499e635b25182e0b04533a0bb0d2"
FREEZE = "9b8c814e29c4862eb99ea51699dde0bbb6d308c5ce20ce0ebdcbcb52bac5630c"
DESTINATION = PureWindowsPath(r"C:\KitSdkCandidates\PrincipalRevolveEvaluation02\Candidate")
HOW = "solidworks.sldprt"
REFUSALS = ("full", "front", "translated-support", "foreign-suffix", "missing-final-path")


def digest(raw):
    return sha256(raw).hexdigest()


def worker(request):
    from convert import open_document, write_document
    from convert.api.ApiContext import GetRegistry
    from convert.adapters.base.WriteOptions import WriteOptions

    for name in ("ascii", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "latin-1"):
        codecs.lookup(name)
    for name in (
        "interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance", "interchange.document.Models.DocumentWalk",
        "interchange.document.Validation.AngleRevValidate", "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate", "interchange.document.Validation.DocumentReferenceValidate",
        "interchange.document.Validation.PlaneRevValidate", "interchange.document.Validation.DistExtValidate",
    ):
        import_module(name)
    emitter = import_module("convert.adapters.solidworks.Core.Writing.EmitNativeMut")
    writer = GetRegistry().GetWriter(HOW)
    name = request.get("variant")
    spec = request["spec"].copy()
    plane = "front" if name == "front" else request["plane"]
    if name == "full":
        spec["angle_deg"] = 360
    alteration = name if name == "translated-support" else None
    options = {"require_native_transfers": True}
    if name != "missing-final-path":
        path = spec["self_path"]
        options["final_destination"] = path[:-7] + ".SLDASM" if name == "foreign-suffix" else path
    emitter.ReadTime = lambda: spec["created_at"]
    active = True
    denied = []

    def audit(event, _args):
        if active and (event in {"open", "os.listdir", "os.scandir", "os.system", "os.fork", "os.posix_spawn"}
                       or event.startswith(("subprocess.", "socket.", "ctypes."))):
            denied.append(event)
            raise RuntimeError("public revolve attempted external access: " + event)

    sys.addaudithook(audit)
    try:
        document = authored_neutral(spec, plane, alteration)
        direct, public = BytesIO(), BytesIO()
        if name:
            initial = b"verified unchanged destination"
            target = BytesIO(initial)
            try:
                write_document(document, target, destination_format=HOW, allow_carrier=False, values=options)
            except (ValueError, TypeError, LookupError) as error:
                assert target.getvalue() == initial and target.tell() == 0 and not denied
                return {"variant": name, "reason": str(error), "runtime_external_attempts": denied}
            raise ValueError("unsupported public revolve unexpectedly emitted")
        assert writer.supports(document, direct)
        direct_receipt = writer.write(document, direct, WriteOptions(configuration="Default", values=options))
        public_receipt = write_document(document, public, destination_format=HOW, allow_carrier=False, values=options)
        assert not denied
    finally:
        active = False
    raw = public.getvalue()
    assert raw == direct.getvalue() and digest(raw) == request["candidate_sha256"]
    for receipt in (direct_receipt, public_receipt):
        assert receipt.path is None and receipt.bytes_written == len(raw)
        assert receipt.vendor_loadable and receipt.application_usable
    assert document.capabilities <= public_receipt.native_capabilities
    result = measure(raw, spec, plane)
    readback = open_document(raw, source_format=HOW, strict=True)
    assert readback.bodies[0].name == document.bodies[0].name
    return {
        "name": spec["name"], "native_candidate_sha256": digest(raw), "length": len(raw),
        "streams": result["archive_streams"], "cold_body_name": readback.bodies[0].name,
        "runtime_external_attempts": denied, "normal_sdk_and_direct_equal": True,
        "native_capabilities": sorted(value.value for value in public_receipt.native_capabilities),
    }


def check(path, expected):
    raw = path.read_bytes()
    assert digest(raw) == expected
    return json.loads(raw)


def main(generation_path, freeze_path, output, revision, tree):
    generation = check(generation_path, GENERATION)
    assert generation["freeze_sha256"] == FREEZE and generation["original_files_read"] == 0
    epoch = check(freeze_path, FREEZE)["write_epoch"]
    requests = []
    for name, row in sorted(generation["cases"].items()):
        intent = row["intent"]
        stem = "Kit" + name
        requests.append({"plane": intent["plane"], "candidate_sha256": row["generated"]["sha256"], "spec": {
            "name": stem, "radial_mm": [value * 1000 for value in intent["radius_m"]],
            "axial_mm": [value * 1000 for value in intent["axial_m"]], "axis_x_mm": intent["axis_x_m"] * 1000,
            "axis_span_mm": [value * 1000 for value in intent["axis_axial_m"]], "angle_deg": intent["angle_deg"],
            "reverse": intent["reverse"], "edit_angle_deg": intent["edit_angle_deg"],
            "created_at": epoch, "self_path": str(DESTINATION / (stem + ".SLDPRT")),
        }})
    assert len(requests) == 2
    controls = [requests[0] | {"variant": value} for value in REFUSALS]
    cases = []
    for request in [*requests, *controls]:
        data = json.dumps(request, sort_keys=True)
        child = run((sys.executable, "-I", "-S", "-B", __file__, "--worker"), input=data,
                    capture_output=True, text=True, check=False, timeout=90)
        if child.returncode or child.stderr:
            raise ValueError(child.stderr)
        cases.append({"request_sha256": digest(data.encode()), **json.loads(child.stdout)})
    proof = {
        "schema": "kit.sw2026.public-principal-revolve-parity.v1", "generation_sha256": GENERATION,
        "source_revision": revision, "source_tree": tree, "proof_tool_sha256": digest(Path(__file__).read_bytes()),
        "fresh_workers": len(cases), "new_native_processes": 0, "cases": cases,
    }
    raw = (json.dumps(proof, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with output.open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"cases": len(cases), "receipt_sha256": digest(raw)}))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--generation", type=Path)
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--revision")
    parser.add_argument("--tree")
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin)), allow_nan=False))
    else:
        main(args.generation, args.freeze, args.output, args.revision, args.tree)
