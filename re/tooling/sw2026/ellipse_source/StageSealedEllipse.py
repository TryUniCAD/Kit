from argparse import ArgumentParser
from io import BytesIO
import json
from pathlib import Path, PureWindowsPath
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from ColdEllipsePacket import GUEST as DISCLOSED_GUEST, TOOLS_COLD, TRIAL, candidate_path, verify as disclosed_plan
from EllipsePacket import CONTROLS, digest, encode, pinned_json, put, sha
from EllipseModel import require
from RunSealedEllipse import ASSETS, CONSTRUCTION, CONSTRUCTION_SRC, DISCLOSED_RESULT_SHA, DISCLOSED_SHA, EVAL_TOOLS
from RunSealedEllipse import ENTRY, FROZEN, GUEST, LOCK_COMMIT, LOCK_SHA, NAME, SCHEMA, SOURCE_ROOT, WRITER_FIRST
from RunSealedEllipse import compiler_members, extract, generate, neutral, verify, verify_disclosed


HERE = Path(__file__).resolve()
FAMILY = "re/tooling/sw2026/ellipse_source"
LOCK_FILE = "re/solidworks/measurements/2026/EllipseBlindBossPrewriterLock01.json"
COMPILER_FILES = {f"{FAMILY}/{name}.py" for name in (
    "BuildColdEllipsePart", "CompileColdEllipse", "ColdEllipseModel", "EllipseArchiveGrammar",
    "EllipseArchiveOwners", "EllipseArchiveCustody", "EllipseModel", "ReplayEllipseArchive",
)} | {"tests/__init__.py", "tests/Convert/__init__.py", "tests/Convert/Solidworks/__init__.py",
      "tests/Convert/Solidworks/Research/ConstructionGuard.py"}
HOST = Path("/Users/odin/Documents/UniCAD/Oracle121Takeover")
DISCLOSED = HOST / "EllipseColdPrototype02"


def git(*args, data=None):
    return subprocess.check_output(("git", *args), cwd=HERE.parents[4], input=data)


def blob(revision, path):
    return git("show", f"{revision}:{path}")


def compiler():
    tree = {}
    for row in git("ls-tree", "-r", "-z", CONSTRUCTION, "src", *sorted(COMPILER_FILES)).split(b"\0"):
        if not row:
            continue
        header, name = row.decode().split("\t", 1)
        mode, kind, object_id = header.split()
        if name.endswith(".py"):
            require((mode, kind) == ("100644", "blob"), "compiler must contain only regular tracked Python")
            tree[name] = object_id
    names = sorted(tree)
    require(COMPILER_FILES <= tree.keys(), "missing exact tracked compiler source")
    data = BytesIO(git("cat-file", "--batch", data=("".join(tree[name] + "\n" for name in names)).encode()))
    compressed = BytesIO()
    with ZipFile(compressed, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name in names:
            oid, kind, length = data.readline().decode().split()
            require((oid, kind) == (tree[name], "blob"), "compiler blob is outside the pinned tree")
            raw = data.read(int(length))
            require(len(raw) == int(length) and data.read(1) == b"\n", "compiler blob boundary differs")
            item = ZipInfo(name, (2020, 1, 1, 0, 0, 0))
            item.create_system, item.external_attr = 3, 0o100644 << 16
            archive.writestr(item, raw, compress_type=ZIP_DEFLATED, compresslevel=9)
        require(not data.read(1), "compiler blob stream has surplus data")
        compiler_members(archive)
    return compressed.getvalue(), len(names)


def write_members(folder, files):
    folder.mkdir()
    for name, data in sorted(files.items()):
        item = folder / name
        item.parent.mkdir(exist_ok=True)
        put(item, data)


def stage(output):
    require(output == HOST / NAME and output.resolve() == output and not output.exists(),
            "use the designated unused public handoff root")
    entry = DISCLOSED / "DisclosedResult.json"
    result = pinned_json(entry, DISCLOSED_RESULT_SHA)
    verify_disclosed(result)
    current = git("rev-parse", "HEAD").decode().strip()
    require(not git("status", "--porcelain", "--untracked-files=no")
            and git("rev-parse", f"{CONSTRUCTION}:src").decode().strip() == CONSTRUCTION_SRC
            and not git("diff", "--name-only", CONSTRUCTION, current, "--", "src", *sorted(COMPILER_FILES)),
            "only the committed immutable construction closure may be staged")
    git("merge-base", "--is-ancestor", LOCK_COMMIT, WRITER_FIRST)
    git("merge-base", "--is-ancestor", WRITER_FIRST, CONSTRUCTION)
    git("merge-base", "--is-ancestor", CONSTRUCTION, current)
    first_time = int(git("show", "-s", "--format=%ct", WRITER_FIRST))
    disclosed_packet = DISCLOSED / "Packet"
    job, cases, _ = disclosed_plan(disclosed_packet / TRIAL, DISCLOSED_SHA)
    require(job["revision"] == CONSTRUCTION and job["src_tree"] == CONSTRUCTION_SRC,
            "disclosed trial used a different construction closure")
    members = {f"Tool/{name}": blob(CONSTRUCTION, f"{folder}/{name}")
               for folder, names in TOOLS_COLD.items() for name in names}
    members.update({name: (disclosed_packet / name).read_bytes() for name in CONTROLS})
    require(all(digest(data) == job["files"][name]["sha256"] for name, data in members.items()),
            "public observer or control differs from the actual disclosed run")
    members.update({f"Tool/{name}": blob(current, f"{FAMILY}/{name}") for name in EVAL_TOOLS})
    members["PrewriterLock.json"] = blob(LOCK_COMMIT, LOCK_FILE)
    require(digest(members["PrewriterLock.json"]) == LOCK_SHA
            and json.loads(members["PrewriterLock.json"])["finished_at"] < first_time,
            "independent source lock must predate the first writer")
    members["DisclosedNativeResult.json"] = entry.read_bytes()
    members["Compiler.zip"], sources = compiler()
    require(set(members) == ASSETS, "operational public member inventory differs")
    freeze = {
        "schema": SCHEMA, "construction_revision": CONSTRUCTION, "construction_src_tree": CONSTRUCTION_SRC,
        "method_revision": current, "first_writer": WRITER_FIRST, "first_writer_time": first_time, "lock_commit": LOCK_COMMIT,
        "source_root": str(SOURCE_ROOT), "evaluation_root": str(GUEST), "disclosed_trial_sha256": DISCLOSED_SHA,
        "disclosed_result_sha256": DISCLOSED_RESULT_SHA, "compiler_members": sources,
        "files": {name: {"bytes": len(value), "sha256": digest(value)} for name, value in members.items()},
    }
    pin = digest(encode(freeze))
    members[FROZEN] = encode(freeze)
    with TemporaryDirectory(prefix="KitEllipseSealedPreflight.", dir="/tmp") as temporary:
        root = Path(temporary).resolve()
        packet = root / "Packet"
        write_members(packet, members)
        verify(packet, pin)
        shallow = root / "RunSealedEllipse.py"
        for name in {path for path in members if path.startswith("Tool/")}:
            put(root / Path(name).name, members[name])
        require(len(shallow.parents) <= 4, "preflight runner must use an actually shallow relocation")
        launched = subprocess.run([sys.executable, "-E", "-B", str(shallow), str(packet), "--pin", pin, "--verify"],
                                  capture_output=True, timeout=15, check=False)
        require(launched.returncode == 0 and not launched.stderr and json.loads(launched.stdout)["freeze_sha256"] == pin,
                "actual shallow relocated guest entry cannot verify its packet")
        denial = subprocess.run([sys.executable, "-I", "-B", str(root / "ReadSealedEllipseSources.py"),
                                 str(packet / "PrewriterLock.json")], capture_output=True, timeout=15, check=False)
        require(denial.returncode == 2 and not denial.stderr and not denial.stdout,
                "protected custody entry did not refuse the host")
        application = extract(packet / "Compiler.zip", root / "Compiler")
        trials = []
        for slot, case in enumerate(cases):
            case_path = candidate_path(case)
            old = DISCLOSED_GUEST / "Packet" / case_path
            target = GUEST / "Capture" / f"Slot{slot + 1:02d}" / PureWindowsPath(old).name
            reference, initial = generate(application, neutral(case, old, slot))
            proof, candidate = generate(application, neutral(case, target, slot))
            repeat = generate(application, neutral(case, target, slot))
            require(sha(disclosed_packet / case_path) == reference["archive_sha256"]
                    and initial == (disclosed_packet / case_path).read_bytes() and repeat == (proof, candidate),
                    "packaged compiler drifted from disclosed bytes or changed under repeat")
            changed = {key for key, value in proof["streams"].items() if value != reference["streams"][key]}
            require(changed == {"Header2", "Contents/Config-0-ModelHeader"},
                    "relocating an otherwise identical ellipse changed model-bearing streams")
            trials.append({"disclosed_sha256": digest(initial), "relocated_sha256": digest(candidate),
                           "streams": len(proof["streams"]), "changed_streams": sorted(changed),
                           "runtime_accesses": proof["runtime_accesses"]})
    output.mkdir()
    write_members(output / "Packet", members)
    (output / "Public").mkdir()
    verify(output / "Packet", pin)
    receipt = {"freeze_sha256": pin, "method_revision": current, "compiler_members": sources,
               "compiler_sha256": digest(members["Compiler.zip"]), "public_assets": len(ASSETS),
               "guarded_writer_processes": 6, "shallow_process_verified": True, "host_custody_refused": True,
               "disclosed_smoke": trials, "private_source_reads": 0, "native_launches": 0, "heldout_credit": 0}
    put(output / "StageEvidence.json", encode(receipt))
    return receipt


if __name__ == "__main__":
    cli = ArgumentParser()
    cli.add_argument("--output", required=True, type=Path)
    print(json.dumps(stage(cli.parse_args().output), sort_keys=True, allow_nan=False))
