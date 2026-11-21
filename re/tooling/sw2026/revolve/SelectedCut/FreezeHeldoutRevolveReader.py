from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path, PureWindowsPath
from shutil import copytree
from subprocess import check_output, run
import json
import os
import sys


HERE = Path(__file__).resolve()
PREFIX = PureWindowsPath(r"C:\KitSdkCandidates")
PATH = "src/convert/adapters/solidworks/Core/TypedResolved/Revolves/SelectedCut/ReadRevWrapper.py"
WORKER = "re/tooling/sw2026/revolve/EndModes/ProveSelectedRevCut.py"
BASE = "bddc42388bd73d41104e779aa22715a661ab7c06"
WRITER = "0cc19e4adcfca7bd55c0ebf0ebf97bf457e234ebe11dd045de07f08a5be43f17"
CANDIDATE = "ecd941c1a9b5a936d26db77efcf68f5ee479457b1e5685c64c004b1b827d6b1a"
NATIVE = "aee4c2213efdd216e35a9c22de36811b83eab06703b9233ef0f06d36619c8084"
DISCLOSURE = "re/solidworks/measurements/2026/SdkAuthoredRevolveFaceCache01.json"
SCHEMA = "kit.sw2026.heldout-selected-revolve-reader-freeze.v1"


def digest(raw):
    return sha256(raw).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def checked(path, pin):
    raw = path.read_bytes()
    require(not path.is_symlink() and digest(raw) == pin, "reader capsule input changed")
    return raw


def publish(path, raw):
    with path.open("xb") as stream:
        stream.write(raw)


def freeze(folder):
    root = HERE.parents[5]

    def git(*args):
        return check_output(("git", *args), cwd=root)

    require(folder.is_absolute() and not folder.is_relative_to(root) and not folder.exists(), "use a fresh external capsule folder")
    revision = git("rev-parse", "HEAD").decode().strip()
    proof = git("show", f"{revision}:{DISCLOSURE}")
    data = json.loads(proof)
    require(data["passed"] and data["strict_reads"] == 8 and data["heldout_credit"] == 0,
            "independent authored route must pass before reopening locked sources")
    before, after = (git("show", f"{rev}:{PATH}") for rev in (BASE, revision))
    require(before != after, "capsule needs the observed wrapper rule")
    names = {"Observe.py": HERE.read_bytes(), "RecheckHeldoutStockCuts.py": HERE.with_name("RecheckHeldoutStockCuts.py").read_bytes(),
             "ScopedRevolveRead.py": after, "DisclosedReaderEvidence.json": proof}
    require(all(names[key] == git("show", f"{revision}:{HERE.with_name(source).relative_to(root).as_posix()}")
                for key, source in (("Observe.py", HERE.name), ("RecheckHeldoutStockCuts.py", "RecheckHeldoutStockCuts.py"))),
            "freeze tools must be committed")
    folder.mkdir()
    for name, payload in names.items():
        publish(folder / name, payload)
    record = encode({"schema": SCHEMA, "writer_freeze_sha256": WRITER, "source_branch_revision": revision,
                     "base_wrapper_sha256": digest(before), "effective_source_overrides": {PATH: digest(after)},
                     "files": {key: digest(raw) for key, raw in names.items()}, "sealed_sources_opened": 0})
    publish(folder / "ReaderFreeze.json", record)
    return {"reader_freeze_sha256": digest(record), "sealed_sources_opened": 0}


def observe(folder, pin):
    require(os.name == "nt" and folder == HERE.parent and folder.name.startswith("ScopedRevolveHeldoutReader"),
            "run the pinned isolated reader capsule on the Windows oracle host")
    manifest = json.loads(checked(folder / "ReaderFreeze.json", pin))
    pins = manifest["files"]
    require(manifest["schema"] == SCHEMA and manifest["writer_freeze_sha256"] == WRITER
            and checked(HERE, pins["Observe.py"]) and checked(folder / "RecheckHeldoutStockCuts.py", pins["RecheckHeldoutStockCuts.py"])
            and json.loads(checked(folder / "DisclosedReaderEvidence.json", pins["DisclosedReaderEvidence.json"]))["passed"]
            and manifest["sealed_sources_opened"] == 0, "reader capsule did not pass its disclosed proof")
    replacement = checked(folder / "ScopedRevolveRead.py", pins["ScopedRevolveRead.py"])
    require(manifest["effective_source_overrides"] == {PATH: digest(replacement)}, "unapproved source change")
    writer = folder.parent / "ScopedRevolveHeldoutEval03"
    sys.path[:0] = [str(writer), str(HERE.parent)]
    from EvaluateHeldoutStockCuts import verify
    from RecheckHeldoutStockCuts import evaluate

    source, _, frozen = verify(writer, WRITER)
    require(source["writer_revision"] == BASE and checked(frozen / PATH, manifest["base_wrapper_sha256"]),
            "reader capsule does not match the intact original writer")
    private = Path(PREFIX / folder.name)
    private.mkdir()
    read_root = private / "Code"
    copytree(frozen, read_root)
    (read_root / PATH).write_bytes(replacement)
    checked(read_root / PATH, digest(replacement))
    worker = read_root / WORKER

    def dispatch(file, input_pin, *, observed):
        payload = encode({"path": str(file), "sha": input_pin, "observed": observed})
        child = run((sys.executable, "-I", "-B", str(worker), "--worker"), input=payload,
                    capture_output=True, timeout=120)
        require(child.returncode == 0 and not child.stderr, child.stderr.decode(errors="replace"))
        return json.loads(child.stdout)

    evidence = {"freeze_sha256": pin, "base_writer_revision": BASE,
                "source_branch_revision": manifest["source_branch_revision"],
                "effective_source_overrides": manifest["effective_source_overrides"],
                "disclosed_result_sha256": pins["DisclosedReaderEvidence.json"]}
    output = private / "ReadRecheck02.json"
    result = evaluate(writer, WRITER, CANDIDATE, NATIVE, read=dispatch, output=output, reader=evidence)
    publish(folder / "ReadRecheck02.json", checked(output, result["sha256"]))
    return result


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("action", choices=("freeze", "observe"))
    parser.add_argument("folder", type=Path)
    parser.add_argument("--pin")
    args = parser.parse_args()
    if args.action == "freeze":
        status = freeze(args.folder)
    else:
        try:
            status = observe(args.folder, args.pin)
        except Exception as error:
            print(json.dumps({"complete": False, "error_type": type(error).__name__}))
            raise SystemExit(1) from None
    print(json.dumps(status, sort_keys=True))
    raise SystemExit(int(not status.get("passed", True)))
