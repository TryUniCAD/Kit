from argparse import ArgumentParser
from hashlib import sha256
from io import BytesIO
from json import dumps, loads
from os import O_APPEND, O_CREAT, O_RDONLY, O_RDWR, O_TRUNC, O_WRONLY, fsdecode
from pathlib import Path
from re import sub
from subprocess import check_output, run
import sys
from tarfile import open as open_tar
from tempfile import TemporaryDirectory

REPO = Path(__file__).resolve().parents[3]
BASE = "f3d8760f214d65fbe71aa4b8bf81a17f553dbb60"
INVENTORY = "1de42ebe8bf52b8403de2e6a73fe45b45ac83484a6532230d4b379aff93ca03f"
PINS = {
    "C130-P01": "d1f9225bfdf31d9708fc8fc8f94261edc9479d01d6a09c720ae70c16a5aa2362",
    "C123-P01": "c965847aa2a1ba6c1bacc43ae0c911db1610e57497ab5ca19fea5e6aed33ada4",
    "C017-P01": "215d76c07e95dd13f791b404eeacd6f625a0bbefa603e3653b007a73a853184c",
}
LENGTH = "freecad:parameter:Pad:Length"
WIDTH = "freecad:parameter:Sketch:constraint:9"
EXPR = "Sketch.Constraints.width / 2"
INPUTS = (
    "src/convert/adapters/freecad/Native.py",
    "src/convert/adapters/freecad/NativeParameters/BindPadExprMut.py",
    "src/convert/adapters/freecad/NativeParameters/FindSketchDim.py",
    "src/convert/adapters/freecad/NativeParameters/LinkPadLength.py",
    "src/convert/adapters/freecad/NativeParameters/ReadPadExpr.py",
)
MUTATIONS = {"os.mkdir", "os.rmdir", "os.remove", "os.rename", "os.link", "os.symlink",
             "os.chmod", "os.truncate", "subprocess.Popen", "os.system", "os.exec",
             "os.fork", "os.posix_spawn", "ctypes.dlopen"}


def digest(raw):
    return sha256(raw).hexdigest()


def wire(value):
    return (dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def guard_source(source, sdk):
    reads = []
    denied = []
    allowed_code = (sdk.resolve(), Path(sys.base_prefix).resolve())
    mode_mask = O_WRONLY | O_RDWR | O_CREAT | O_TRUNC | O_APPEND

    def guard(event, args):
        if event == "open":
            path_arg, _, flags = args
            if not isinstance(path_arg, (str, bytes)) or flags & mode_mask != O_RDONLY:
                denied.append(event)
                raise PermissionError("unexpected source worker open")
            path = Path(fsdecode(path_arg)).resolve()
            if path == source:
                reads.append(event)
            elif path.suffix not in {".py", ".pyc", ".so", ".pyd"} or not any(
                path.is_relative_to(root) for root in allowed_code
            ):
                denied.append(event)
                raise PermissionError("unexpected source worker read")
        elif event in MUTATIONS:
            denied.append(event)
            raise PermissionError("unexpected source worker operation")

    sys.addaudithook(guard)
    return reads, denied


def normalize(doc, replay_field):
    model = loads(doc.to_json(indent=None))
    length, = (p for p in model["parameters"]["$tuple"] if p["id"] == LENGTH)
    length["expression"]["parameter_ids"] = {"$tuple": []}
    notes = model["diagnostics"]["$tuple"]
    removed = [n for n in notes if n["code"] == "freecad.sheet_alias.unresolved"
               and n["attributes"].get("counts") == {"unsupported_reference": 1}]
    model["diagnostics"]["$tuple"] = [n for n in notes if n not in removed]
    for payload in model["brep_payloads"]["$tuple"]:
        payload["attributes"].pop(replay_field, None)
    return digest(wire(model)), len(removed)


def worker(request):
    sdk = Path(request["sdk"]).resolve()
    source = Path(request["source"])
    assert source == source.resolve(strict=True)
    sys.path.insert(0, str(sdk))
    from convert import open_document
    from convert.adapters.freecad.Replay.NativeIdentity import KReplaySemanticAttr
    from convert.adapters.freecad.Replay.SemanticDigest import SemanticDigest

    assert not any(word in sub(r"[\W_]+", "", source.as_posix().casefold())
                   for word in ("sealed", "heldout", "holdout"))
    assert source.suffix.casefold() == ".fcstd" and digest(source.read_bytes()) == request["pin"]
    reads, denied = guard_source(source, sdk)
    doc = open_document(source, source_format="freecad.fcstd", strict=True,
                        include_brep=True, include_tessellation=True)
    source_reads = len(reads)
    assert source_reads and not denied
    assert digest(source.read_bytes()) == doc.source.sha256 == request["pin"]
    doc.assert_valid()
    sketch, = doc.sketches
    pad, = doc.feature_timeline
    width, = (p for p in doc.parameters if p.id == WIDTH)
    length, = (p for p in doc.parameters if p.id == LENGTH)
    assert pad.sketch_id == sketch.id == width.owner_id
    assert not pad.suppressed and not sketch.suppressed
    assert length.owner_id == pad.id and length.id in pad.parameter_ids
    assert sketch.constraints[9].parameter_id == width.id and width.id in sketch.parameter_ids
    assert width.value.value == 40.0 and length.value.value == 20.0
    assert width.value.unit == length.value.unit == "mm"
    assert length.expression is not None and length.expression.source == EXPR
    assert length.expression.language == "freecad"
    semantic_values = [p.attributes[KReplaySemanticAttr] for p in doc.brep_payloads
                       if KReplaySemanticAttr in p.attributes]
    assert semantic_values == [SemanticDigest(doc)]
    normalized, diagnostics = normalize(doc, KReplaySemanticAttr)
    assert not denied
    return {
        "dependency_ids": list(length.expression.parameter_ids),
        "normalized_whole_document_sha256": normalized,
        "unsupported_reference_diagnostics": diagnostics,
        "saved_width_mm": width.value.value,
        "saved_length_mm": length.value.value,
        "saved_expression": length.expression.source,
        "provided_source_reads": source_reads,
        "source_immutable": True,
        "stored_replay_digest_matches": True,
        "forbidden_events": len(denied),
    }


def process(sdk, row):
    request = {"sdk": str(sdk), "source": row["source_path"], "pin": row["sha256"]}
    result = run((sys.executable, "-I", "-B", __file__, "--worker"),
                 input=wire(request), stdout=-1, stderr=-1, timeout=90, check=False)
    if result.returncode or result.stderr:
        raise ValueError(f"{row['case_id']} guarded source worker failed: {result.stderr.decode().strip()}")
    return loads(result.stdout)


def measure(census):
    raw = (census / "VerifiedInputs01.json").read_bytes()
    assert digest(raw) == INVENTORY
    inputs = {row["case_id"]: row for row in loads(raw)["files"] if row["case_id"] in PINS}
    assert {label: row["sha256"] for label, row in inputs.items()} == PINS
    base_archive = check_output(("git", "-C", str(REPO), "archive", BASE, "src"))
    results = {}
    with TemporaryDirectory(prefix="KitLocalSketchExpr") as folder:
        root = Path(folder)
        with open_tar(fileobj=BytesIO(base_archive), mode="r:") as archive:
            archive.extractall(root, filter="data")
        for label, row in inputs.items():
            before = process(root / "src", row)
            after = process(REPO / "src", row)
            assert before["dependency_ids"] == [] and after["dependency_ids"] == [WIDTH]
            assert before["unsupported_reference_diagnostics"] == 1 and after["unsupported_reference_diagnostics"] == 0
            assert before["normalized_whole_document_sha256"] == after["normalized_whole_document_sha256"]
            results[label] = {"input_sha256": PINS[label], "baseline": before, "linked": after}
    return {
        "schema": "kit.freecad.native-pad-sketch-expression.v1",
        "baseline_revision": BASE,
        "inventory_sha256": INVENTORY,
        "method_sha256": digest(Path(__file__).read_bytes()),
        "production_source_sha256": {name: digest((REPO/name).read_bytes()) for name in INPUTS},
        "disclosed_results": results,
        "fresh_processes": 6,
        "native_products": 0,
        "native_processes": 0,
        "production_corpus_credit": 0,
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--census", type=Path)
    parser.add_argument("--output", type=Path)
    options = parser.parse_args()
    if options.worker:
        try:
            print(dumps(worker(loads(sys.stdin.buffer.read())), sort_keys=True))
        except Exception as error:
            print(type(error).__name__, file=sys.stderr)
            raise SystemExit(1) from None
        return
    if options.census is None or options.output is None:
        parser.error("--census and --output are required")
    result = wire(measure(options.census))
    with options.output.open("xb") as stream:
        stream.write(result)
    print(digest(result))


if __name__ == "__main__":
    main()
