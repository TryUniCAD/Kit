from argparse import ArgumentParser
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path, PureWindowsPath
import re
from shutil import copyfile
import subprocess
import tarfile
from tempfile import TemporaryDirectory


ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"
IMPORTED = "13f1ef12ab727323a826ead989087079f44e9b24a4326aa9b65be61c9d81f325"
RESEARCH = Path("re/tooling/sw2026")
IMPORT = RESEARCH / "imported_body_source"
GUARD = Path("tests/Convert/Solidworks/Research/ConstructionGuard.py")
SUPPORT = ("AuthorCurves.py", "AuthorRectangleAnchors.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py")
PROBES = ("ObserveLocalImportedPart.py", "AuthorImportedBody.py", "RunImportedBodySources.py", "ObserveKernelBodyRestore.py")


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def json_data(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def pinned_tree(repo, revision, directory):
    names = ("tests/__init__.py", "tests/Convert/__init__.py", "tests/Convert/Solidworks/__init__.py",
             "tests/Convert/Solidworks/Research/__init__.py")
    tracked = subprocess.check_output(["git", "ls-tree", "--name-only", "-r", revision, "--", *names], cwd=repo, text=True)
    data = subprocess.check_output(["git", "archive", revision, "--", "src", str(RESEARCH), str(GUARD), *tracked.splitlines()], cwd=repo)
    with tarfile.open(fileobj=BytesIO(data)) as archive:
        archive.extractall(directory, filter="data")


def build_candidates(root, folder, guest, ambient, completed):
    runner = root / IMPORT / "BuildImportedLocalPart.py"
    pypath = os.pathsep.join(map(str, (root / "src", root, root / RESEARCH, root / RESEARCH / "serial")))
    env = os.environ | {"PYTHONPATH": pypath}
    argv = ["uv", "run", "--offline", "--no-project", "--python", "3.13", "python", "-B", str(runner), str(guest / "Candidates")]
    authored = ["--ambient"] if ambient else []
    status = ["--completed"] if completed else []
    first = subprocess.check_output([*argv, *authored, *status], cwd=root, env=env)
    with_artifacts = subprocess.check_output([*argv, *authored, *status, "--artifacts", str(folder / "Candidates")], cwd=root, env=env)
    require(first == with_artifacts, "independent generated probe builds differ")
    build = json.loads(first)
    require(build["runtime_input_file_reads"] == 0 and build["heldout_payloads_read"] == 0,
            "generated probe used an external or sealed input")
    for name, case in build["cases"].items():
        require(digest((folder / "Candidates" / (name + ".SLDPRT")).read_bytes()) == case["sha256"], "candidate changed")
    if ambient or completed:
        baseline = subprocess.check_output([*argv, *(authored if completed else [])], cwd=root, env=env)
        (folder / "Comparison.json").write_bytes(baseline)
    (folder / "Build.json").write_bytes(first)
    return digest(first)


def stage(args):
    repo = Path(__file__).resolve().parents[4]
    folder = args.destination.resolve()
    require(not folder.exists() and not folder.is_relative_to(repo), "use an unused external destination")
    require(re.fullmatch(r"[a-f0-9]{40}", args.revision), "supply a committed full revision")
    guest = args.guest_root
    require(guest.drive.casefold() == "c:" and len(guest.parts) == 2 and re.fullmatch(r"KitImportedProbe[0-9]{2}", guest.name),
            "use a new guest-local import probe directory")
    controls = ((args.control, "Control.SLDPRT", CONTROL), (args.imported_control, "ImportedControl.SLDPRT", IMPORTED))
    for source, _, checksum in controls:
        require(digest(source.read_bytes()) == checksum, "control hash differs")
    folder.mkdir()
    tools = folder / "Tools"
    tools.mkdir()
    for source, name, checksum in controls:
        copyfile(source, folder / name)
        require(digest((folder / name).read_bytes()) == checksum, "control changed during staging")
    with TemporaryDirectory(prefix="kit-local-import-") as temporary:
        root = Path(temporary)
        pinned_tree(repo, args.revision, root)
        build_sha = build_candidates(root, folder, guest, args.ambient, args.completed)
        hashes = {}
        for source in (*(root / RESEARCH / name for name in SUPPORT), *(root / IMPORT / name for name in PROBES)):
            data = source.read_bytes()
            (tools / source.name).write_bytes(data)
            hashes[source.name] = digest(data)
    job = json_data({"schema": "kit.sw2026.imported-local-part-native-job.v1", "writer_revision": args.revision,
                     "guest_root": str(guest), "build_sha256": build_sha, "oracle_sha256": ORACLE, "tools": hashes})
    (folder / "Job.json").write_bytes(job)
    print(json.dumps({"job_sha256": digest(job), "build_sha256": build_sha, "writer_revision": args.revision}))


if __name__ == "__main__":
    parser = ArgumentParser(description="Stage two identical guarded builds and the exact native local import probe")
    parser.add_argument("destination", type=Path)
    parser.add_argument("guest_root", type=PureWindowsPath)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--imported-control", type=Path, required=True)
    parser.add_argument("--ambient", action="store_true")
    parser.add_argument("--completed", action="store_true")
    stage(parser.parse_args())
