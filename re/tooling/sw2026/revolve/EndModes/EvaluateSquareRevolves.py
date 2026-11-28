from argparse import ArgumentParser
from hashlib import sha256
from io import BytesIO
from pathlib import Path, PurePosixPath, PureWindowsPath
from subprocess import check_output
from zipfile import ZIP_DEFLATED, ZipFile
import json
import sys
import time


HOST = Path("/Users/odin/Documents/UniCAD/Oracle121Takeover")
SHARE = PureWindowsPath(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover")
LOCAL = PureWindowsPath(r"C:\KitSdkCandidates")
TOOLS = "re/tooling/sw2026/"
SELF = TOOLS + "revolve/EndModes/EvaluateSquareRevolves.py"
WRITER = "bc49a5acff6c3a5488b47623f6e2353f7cfad2be"
LOCK = "re/solidworks/measurements/2026/RevolveEqualLengthSourceLock01.json"
LOCK_COMMIT = "c9d64090b37b2fa56971662f926441aa9bb2be1f"
LOCK_PIN = "f083f56d7dad630ae2fbebda1c983ce06c8e5c935ace81317dc0f050b561cd53"
SCHEMA = "kit.sw2026.square-revolve-comparison.v1"


def digest(raw):
    return sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def checked(path, pin):
    data = path.read_bytes()
    if digest(data) != pin:
        raise ValueError("square comparison input changed: " + path.name)
    return data


def publish(path, data):
    with path.open("xb") as handle:
        handle.write(data)
    return digest(data)


def freeze(name, split):
    root = Path(__file__).resolve().parents[5]
    assert name.startswith("SquareComparison") and name.isalnum()
    fixture = "RevolveEqualHeldout01" if split == "heldout" else "RevolveEqualDiscovery01"

    def git(*args):
        return check_output(("git", "-C", str(root), *args))

    method = git("rev-parse", "HEAD").decode().strip()
    writer = git("rev-parse", WRITER).decode().strip()
    writer_tree = git("rev-parse", writer + ":src").decode().strip()
    git("merge-base", "--is-ancestor", LOCK_COMMIT, writer)
    git("merge-base", "--is-ancestor", writer, method)
    if split == "heldout":
        lock_data = git("show", method + ":" + LOCK)
        assert digest(lock_data) == LOCK_PIN
    else:
        lock_data = (HOST / fixture / "Capture" / "SourceLock.json").read_bytes()
    lock = json.loads(lock_data)
    assert lock["passed"] and lock["split"] == split and lock["distinct_processes"] == 8
    assert lock["writer_output_count"] == 0 and len(lock["sources"]) == 2
    assert lock["finished_at"] < int(git("show", "-s", "--format=%ct", writer))
    assert all(case["passed"] and not case["reused_authored_phase"] for case in lock["sources"])
    paths = {path for path in git("ls-tree", "-r", "--name-only", method, TOOLS + "revolve/").decode().splitlines()
             if path.endswith(".py") and path.startswith(tuple(TOOLS + "revolve/" + name + "/" for name in
                     ("EndModes", "Preparation", "PrincipalReader", "PrincipalWriter")))}
    paths.update(TOOLS + path for path in ("InspectSquareRevolves.py", "InspectRevolveRelations.py",
                 "InspectGeneratedRevolveEnds.py", "AuthorEqualLengthRevolves.py", "AuthorRevolveEnds.py",
                 "AuthorRevolveSources.py", "AuthorCurves.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py"))
    files = {path: git("show", method + ":" + path) for path in sorted(paths)}
    assert files[SELF] == Path(__file__).read_bytes()
    build = TOOLS + "revolve/EndModes/BuildSquareRevolves.py"
    assert files[build] == git("show", writer + ":" + build)
    archive = BytesIO()
    with ZipFile(BytesIO(git("archive", "--format=zip", writer, "src")), "r") as source:
        with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=6) as target:
            for path in source.namelist():
                if not path.endswith("/"):
                    target.writestr(path, source.read(path))
            for path, data in files.items():
                target.writestr(path, data)
    packet = HOST / name
    packet.mkdir()
    pin = publish(packet / "Code.zip", archive.getvalue())
    lock_pin = publish(packet / "SourceLock.json", lock_data)
    result = {"schema": SCHEMA, "method_revision": method, "writer_revision": writer,
              "writer_source_tree": writer_tree, "split": split, "archive_sha256": pin,
              "lock_sha256": lock_pin, "module_sha256": digest(files[SELF]), "frozen_at": time.time(),
              "packet": str(SHARE / name), "private": str(LOCAL / name), "fixture": fixture,
              "sealed_inputs_opened_while_freezing": 0}
    publish(packet / "EvaluateSquareRevolves.py", files[SELF])
    return {"freeze_sha256": publish(packet / "Freeze.json", encode(result)), "writer_source_tree": writer_tree}


def evaluate(packet, pin):
    manifest = json.loads(checked(packet / "Freeze.json", pin))
    assert manifest["schema"] == SCHEMA and manifest["sealed_inputs_opened_while_freezing"] == 0
    assert Path(manifest["packet"]).resolve() == packet.resolve()
    assert digest(Path(__file__).read_bytes()) == manifest["module_sha256"]
    lock_pin = manifest["lock_sha256"]
    lock = json.loads(checked(packet / "SourceLock.json", lock_pin))
    if manifest["split"] == "heldout":
        assert lock_pin == LOCK_PIN
    private = Path(manifest["private"])
    private.mkdir()
    code = private / "Code"
    with ZipFile(BytesIO(checked(packet / "Code.zip", manifest["archive_sha256"]))) as zipped:
        paths = zipped.namelist()
        assert len(set(path.casefold() for path in paths)) == len(paths)
        assert all(PurePosixPath(path).parts[0] in ("src", "re")
                   and ".." not in PurePosixPath(path).parts and "\\" not in path and ":" not in path
                   for path in paths)
        zipped.extractall(code)
        assert Path(code / SELF).read_bytes() == Path(__file__).read_bytes()
    sys.path[:0] = [str(code / TOOLS), str(code / TOOLS / "revolve" / "EndModes")]
    from AuthorRevolveEnds import read_constants
    from BuildSquareRevolves import build_cases, prepare_cases
    from InspectFresh import healthy, inspect
    from InspectGeneratedRevolveEnds import run_candidate, run_cycle
    from InspectRevolveRelations import constraint_codes
    from InspectSquareRevolves import FullSquareObserver
    import Swapp

    original_root = Path(LOCAL / manifest["fixture"])
    spec = json.loads(checked(Path(SHARE / manifest["fixture"] / "Tool" / "Spec.json"), lock["spec_sha256"]))
    assert spec["split"] == manifest["split"] and lock["split"] == spec["split"]
    assert not Swapp.application_pids() and not Swapp.owned_process_ids()
    FullSquareObserver.constants = read_constants()
    FullSquareObserver.codes = constraint_codes()
    control = Path(SHARE / "GeneratedOrdinaryRevolveNative01" / "Control" / "RevolveFull.SLDPRT")
    checked(control, lock["control_sha256"])
    oracle = lock["oracle_sha256"]
    controls = {}
    phases = []
    outcomes = {}

    def remember(rows):
        phases.extend(row["oracle_identity"]["process_creation_filetime"] for row in rows
                      if "oracle_identity" in row)

    def control_check(label):
        receipt = inspect(control)
        remember([receipt])
        controls[label] = {"passed": healthy(receipt) and receipt["sha256"] == lock["control_sha256"]
                           and receipt["oracle_identity"]["sha256"] == oracle,
                           "sha256": publish(private / (label + ".json"), encode(receipt))}

    prepared = prepare_cases(spec, lock, original_root)
    generated = private / "Generated"
    generated.mkdir()
    results = build_cases(prepared, generated, int(manifest["frozen_at"]))
    generated_rows = {}
    for name, raw, proof in results:
        assert publish(generated / (name + ".SLDPRT"), raw) == proof["candidate_sha256"]
        generated_rows[name] = proof
    build_pin = publish(private / "Generation.json", encode(generated_rows))
    try:
        control_check("before")
        if controls["before"]["passed"]:
            for case, _ in prepared:
                name = case["name"]
                proof = generated_rows[name]
                original = original_root / name / (name + ".SLDPRT")
                reference = private / (name + "-source")
                row = {"passed": False, "source_sha256": proof["source_sha256"],
                       "candidate_sha256": proof["candidate_sha256"],
                       "exact_streams": len(proof["candidate_streams"])}
                outcomes[name] = row
                try:
                    sources, hashes = run_cycle(case, original, proof["source_sha256"], reference, oracle, FullSquareObserver)
                    remember(sources)
                    row["source_phases"] = hashes
                    if len(sources) != 2 or not all(source["passed"] for source in sources):
                        row["reference_failure"] = [source["first_failure"] for source in sources]
                        continue
                    files = {"original": str(reference / "Initial.json"), "original_sha256": hashes[0],
                             "edited": str(reference / "FreshReopen.json"), "edited_sha256": hashes[1],
                             "candidate": str(generated / (name + ".SLDPRT")),
                             "candidate_sha256": proof["candidate_sha256"]}
                    measured, open_rows = run_candidate(case, files, private / name, oracle, FullSquareObserver)
                    remember(open_rows)
                    row.update(candidate_phases=measured["native_phase_sha256"],
                               passed=measured["passed"], failure=measured.get("first_failure"),
                               native_phase_failures=measured["native_phase_failures"],
                               comparisons={label: {"tree_rows": observation["tree_rows"],
                                                    "mass_checks": observation["mass_checks"], "relation_count": 5}
                                            for label, observation in measured["comparisons"].items()})
                    checked(original, proof["source_sha256"])
                except Exception as error:
                    row.update(passed=False, failure_type=type(error).__name__, failure=str(error))
    finally:
        control_check("after")
    idle = not Swapp.application_pids() and not Swapp.owned_process_ids()
    checked(control, lock["control_sha256"])
    passed = (len(phases) == len(set(phases)) == 10 and idle and len(outcomes) == 2
              and all(row["passed"] for row in controls.values()) and all(row["passed"] for row in outcomes.values()))
    report = {"schema": SCHEMA, "freeze_sha256": pin, "source_lock_sha256": lock_pin,
              "writer_revision": manifest["writer_revision"], "writer_source_tree": manifest["writer_source_tree"],
              "method_revision": manifest["method_revision"], "generation_sha256": build_pin,
              "oracle_sha256": oracle, "build": "34.5.2.0604", "split": spec["split"],
              "controls": controls, "distinct_processes": len(set(phases)), "application_idle": idle,
              "writer_external_access_attempts": 0, "heldout_writer_cases_qualified": 2 if passed and spec["split"] == "heldout" else 0,
              "passed": passed, "cases": outcomes}
    return {"passed": passed, "distinct_processes": len(set(phases)),
            "receipt_sha256": publish(packet / "NativeReceipt.json", encode(report))}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("action", choices=("freeze", "evaluate"))
    parser.add_argument("packet")
    parser.add_argument("--pin")
    parser.add_argument("--split", choices=("discovery", "heldout"))
    args = parser.parse_args()
    value = freeze(args.packet, args.split) if args.action == "freeze" else evaluate(Path(args.packet), args.pin)
    print(json.dumps(value, sort_keys=True))
    raise SystemExit(int(value.get("passed") is False))
