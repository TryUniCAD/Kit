from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
import os
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
import sys
from tarfile import open as open_tar


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
REVISION = "2393c3a8106e83ee90e977fb167d27900e5f4f2a"
FOLDERS = ("src", "re/tooling/sw2026", "tests/Convert/Solidworks")
PARENT = "PublicPlanarPair2.SLDASM"
CHILD = "PublicDatumPrism.SLDPRT"
EPOCH = 1794001000
SCHEMA = "kit.sw2026.disclosed-planar-default-registry.v1"


def require(check, message):
    if not check:
        raise ValueError(message)


def fingerprint(data):
    return {"bytes": len(data), "sha256": sha256(data).hexdigest()}


def file_sha(path):
    return fingerprint(path.read_bytes())["sha256"]


def write(path, value):
    with path.open("xb") as file:
        file.write((json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())
    return file_sha(path)


def load(path, wanted):
    require(path.is_file() and not path.is_symlink() and file_sha(path) == wanted,
            "a frozen file does not match its binding: " + path.name)
    return json.loads(path.read_bytes())


def bind(root):
    sys.path[:0] = [str(root / "src"), str(root), str(root / "re/tooling/sw2026"), str(HERE.parent)]


def native_parent(value):
    path = PureWindowsPath(value)
    require(path.is_absolute() and path.name == PARENT and str(path) == value
            and not any(part in (".", "..") for part in value.split("\\")),
            "the encoded final parent must be the canonical exact disclosed Windows basename")
    return path


def snapshot(output):
    from shutil import copyfile

    require(not output.exists() and not output.is_relative_to(ROOT),
            "choose an unused disclosed output directory outside the checkout")
    output.mkdir(parents=False)
    code = output / "CodeRoot"
    code.mkdir()
    for folder in FOLDERS:
        data = check_output(
            ("git", "archive", "--prefix=" + folder + "/", REVISION + ":" + folder),
            cwd=ROOT,
        )
        with open_tar(fileobj=BytesIO(data)) as archive:
            archive.extractall(code, members=(row for row in archive.getmembers()
                                              if row.isfile() and row.name.endswith(".py")), filter="data")
    for relative in ("tests/__init__.py", "tests/Convert/__init__.py"):
        (code / relative).write_bytes(check_output(("git", "show", REVISION + ":" + relative), cwd=ROOT))
    tools = code / "re/tooling/sw2026/planar_registry"
    tools.mkdir(exist_ok=True)
    for name in ("PlanarRegistryBuild.py", "RectanglePresentation.py",
                 "ObservePlanarRegistry.py", "PlanarPriorAdmission.py"):
        copyfile(HERE.with_name(name), tools / name)
    code_hashes = {
        path.relative_to(code).as_posix(): file_sha(path)
        for path in sorted(code.rglob("*.py"))
    }
    return code, write(output / "CodeManifest.json", {"revision": REVISION, "files": code_hashes})


def artifact(candidate):
    return {**fingerprint(candidate.BytesValue), "streams": {
        name: fingerprint(data) for name, data in sorted(candidate.StreamsValue.items())
    }}


def prepare_memory():
    bind(ROOT)
    from convert.adapters.solidworks.Core.AssemblyPreparation.PrepareAssembly import PrepareAssembly
    from interchange.serialization.Deserialize import FromData
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

    value = json.load(sys.stdin)
    require(set(value) == {"document", "native_parent", "saved_at"} and value["saved_at"] == EPOCH,
            "the guarded preparation needs only the explicit disclosed intent")
    document = FromData(value["document"])
    for module in (
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentValidate",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(module)
    for name in ("utf-8", "utf-8-sig", "utf-16-le", "latin-1", "ascii"):
        lookup(name)
    document.assert_valid()
    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    sys.addaudithook(audit.InspectEvent)
    audit.BeginBuild()
    result = PrepareAssembly(document, str(native_parent(value["native_parent"])), EPOCH)
    require(not audit.DeniedReads, "the internal control read runtime input")
    return {"pass": True, "pid": os.getpid(), "runtime_input_reads": 0,
            "files": {PARENT: artifact(result), CHILD: artifact(result.ChildValue)}}


def subtask(args, incoming=None):
    result = run((sys.executable, "-I", "-B", *map(str, args)), input=incoming,
                 capture_output=True, timeout=120, check=False)
    require(result.returncode == 0, result.stderr.decode(errors="replace"))
    return json.loads(result.stdout)


def issued_files(directory, memory):
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    result = {}
    for name in (PARENT, CHILD):
        data = (directory / name).read_bytes()
        streams = SldprtArchive.from_bytes(data).streams
        record = {**fingerprint(data), "streams": {
            key: fingerprint(value) for key, value in sorted(streams.items())
        }}
        require(record == memory[name], "normal registry changed the prospective constructor bytes")
        result[name] = record
    return result


def prove_archives(code, directory, prediction, memory):
    bind(code)
    from interchange.document.Models.DocumentModel import CadDocument
    from ReadSdkPlanarGroupNative import audit, compare
    from ReadSdkOrderedNative import read_process
    from RectanglePresentation import differences, observe

    files = issued_files(directory, memory)
    read = read_process(code, directory / PARENT)
    projected = compare(CadDocument.from_json(read["document_json"]), prediction,
                        False, files[CHILD]["sha256"])
    target_display = observe((directory / CHILD).read_bytes())
    dims = prediction["child_dimensions_m"]
    wanted_text = {"width": [0., -.75 * dims["height"], 0.],
                   "height": [.75 * dims["width"], 0., 0.]}
    require(not differences(wanted_text, {axis: row["text_m"] for axis, row in target_display.items()}),
            "actual generated label placement differs from the independent disclosed intent")
    expected_delta = {
        "width": [-.15 * dims["width"], -dims["height"] / 2 - .0067, 0.],
        "height": [dims["width"] / 2 + .0082, .11 * dims["height"], 0.],
    }
    earlier = differences(expected_delta, {axis: row["text_m"] for axis, row in target_display.items()})
    require(len(earlier) == 4, "the legacy explicit label formula was not distinguished")
    audits = {name: audit(code, directory / name) for name in (PARENT, CHILD)}
    return {
        "files": files, "strict_public_read": projected, "actual_child_display": target_display,
        "prior_recipe_formula_on_disclosed_dimensions": expected_delta,
        "prior_recipe_formula_comparison": {"qualified": False, "differences": earlier},
        "linked_archive_replays": {name: row["typed_stream_round_trips"] for name, row in audits.items()},
    }


def build(output, locator):
    code, code_sha = snapshot(output)
    bind(code)
    from interchange.serialization.EncodeData import ToData
    from MakeAssemblyBoundaryCase import make_case
    from PortableAsmPrediction import predict

    request = {"document": ToData(make_case(2)), "native_parent": str(native_parent(locator)), "saved_at": EPOCH}
    expected = predict(request)
    require(tuple(map(len, (expected["tree"]["parent"], expected["tree"]["child"]))) == (26, 25),
            "disclosed profile has another independently predicted tree")
    request_sha = write(output / "NeutralRequest.json", request)
    pred_sha = write(output / "Prediction.json", expected)
    memory = subtask(
        (code / "re/tooling/sw2026/planar_registry/PlanarRegistryBuild.py", "memory"),
        json.dumps(request, separators=(",", ":"), allow_nan=False).encode(),
    )
    worker_request = {
        **request, "expected_sha256": {name: record["sha256"] for name, record in memory["files"].items()},
    }
    incoming = output / "WorkerInput.json"
    worker_sha = write(incoming, worker_request)
    script = code / "re/tooling/sw2026/PublicAssemblyRegistryProcess.py"
    reports = {mode: subtask((script, code, mode, 2, output / directory, incoming))
               for mode, directory in (("fresh", "FrozenGenerated"), ("explicit", "AliasReplay"),
                                       ("unqualified-child", "RejectedChild"), ("stream-rejected", "RejectedStream"))}
    require(len({memory["pid"], *(row["worker_pid"] for row in reports.values())}) == 5
            and all(row["passed"] and row["runtime_input_file_reads"] == 0 for row in reports.values()),
            "the genuine public or refusal process checks did not pass")
    verified = prove_archives(code, output / "FrozenGenerated", expected, memory["files"])
    require(issued_files(output / "AliasReplay", memory["files"]) == verified["files"],
            "the explicit alias does not preserve all generated bytes")
    fixture = {
        "schema": SCHEMA, "revision": REVISION, "code_manifest_sha256": code_sha,
        "request_sha256": request_sha, "prediction_sha256": pred_sha,
        "worker_input_sha256": worker_sha, "native_parent": locator,
        "writer_processes": reports, **verified, "runtime_input_file_reads": 0,
        "native_processes_started": 0, "native_acceptance": False,
        "prior_source_inputs_read": 0, "new_heldout_credit": 0,
        "python": sys.version, "interpreter_sha256": file_sha(Path(sys.executable)),
    }
    fixture_sha = write(output / "Fixture.json", fixture)
    return {"fixture_sha256": fixture_sha, "code_manifest_sha256": code_sha,
            "files": verified["files"], "native_parent": locator, "processes": 5,
            "native_acceptance": False, "new_heldout_credit": 0}


def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "memory"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--native-parent")
    args = parser.parse_args()
    if args.mode == "memory":
        result = prepare_memory()
    else:
        require(args.output is not None and args.native_parent is not None,
                "prepare requires a fresh host packet and exact native locator")
        result = build(args.output.resolve(), args.native_parent)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
