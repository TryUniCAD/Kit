from argparse import ArgumentParser
from ast import parse
from copy import deepcopy
from io import BytesIO
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
import json
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from PatternParityPacket import (
    BUILD, DEFAULT_SMOKE, GUARD, PRIOR_FREEZE, PRIOR_RESULT, PRIOR_TRIAL, SCHEMA, SDK_REVISION,
    SDK_TREE, SLOTS, TRIAL, WORKER, checked, check_product, check_request, digest, encode, exclusive,
    identity, invoke, pinned_result, require, safe_python, unpack_sources, verified_packet,
)


ROOT = HERE.parents[6]
TOOL_PATH = HERE.parent.relative_to(ROOT).as_posix()
TOOLS = ("PatternDefaultWorker.py", "PatternParityPacket.py", "RunPatternDefaultParity.py", HERE.name)
GUARD_PACKAGES = tuple(f"{name}/__init__.py" for name in
                       ("tests", "tests/Convert", "tests/Convert/Solidworks", "tests/Convert/Solidworks/Research"))
DISCLOSED = "GeneratedLocalPatternNative02"
DISCLOSED_FREEZE = "da60bbfdc5411448b9aa5cd06c2a8772a0e0f2c39efa14ba2dc336c625e32cb1"
DISCLOSED_BUILD = "b04e279af46524b69a3198c50e2ba06a89702327be1885eb5e2283d82f2d84a3"
DISCLOSED_RESULT = "ae4f5853e4066a0d3f00cf4cbdaac12797b18c55c268ada6431d7e062bd5d23b"
TRACE = """
import json, runpy, sys
from pathlib import Path
p = Path(sys.argv[1])
root = Path(sys.argv[2])
seen = {str(p)}
def audit(event, args):
    if event == 'open' and type(args[0]) is str and args[0].endswith('.py'):
        name = Path(args[0])
        if name.is_absolute() and name.is_relative_to(root):
            seen.add(str(name))
sys.addaudithook(audit)
sys.argv = [str(p), sys.argv[3]]
runpy.run_path(str(p), run_name='__main__')
sys.stderr.write(json.dumps(sorted(seen)))
"""


def git(*args):
    return check_output(("git", *args), cwd=ROOT)


def tracked_sources(tool_revision):
    paths = "src", "re/tooling/sw2026", GUARD, *GUARD_PACKAGES
    rows = git("ls-tree", "-r", "-z", SDK_REVISION, *paths).decode().rstrip("\0").split("\0")
    inventory = {}
    for record in rows:
        metadata, name = record.split("\t", 1)
        if not name.endswith(".py"):
            continue
        mode, kind, blob = metadata.split()
        require(mode in ("100644", "100755") and kind == "blob", "frozen source includes a Python link")
        safe_python(name)
        inventory[name] = blob
    for leaf in TOOLS:
        name = TOOL_PATH + "/" + leaf
        metadata, exact = git("ls-tree", tool_revision, name).decode().strip().split("\t", 1)
        mode, kind, blob = metadata.split()
        require(name == exact and kind == "blob" and mode == "100644"
                and git("show", f"{tool_revision}:{name}") == (HERE.parent / leaf).read_bytes(),
                "staging needs the exact committed research tools")
        inventory[name] = blob
    batch = ("\n".join(inventory.values()) + "\n").encode()
    result = run(("git", "cat-file", "--batch"), cwd=ROOT, input=batch, capture_output=True, timeout=60, check=True)
    sources = {}
    data = BytesIO(result.stdout)
    for name, expected in inventory.items():
        blob, kind, length = data.readline().decode().split()
        require(blob == expected and kind == "blob", "frozen Python blob differs")
        raw = data.read(int(length))
        require(len(raw) == int(length) and data.read(1) == b"\n", "incomplete frozen Python blob")
        sources[name] = raw
    require(not result.stderr and not data.read(), "unexpected Python closure transport")
    return sources


def materialize(files, root):
    for name, raw in files.items():
        target = root.joinpath(*safe_python(name).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        exclusive(target, raw)
    return root / WORKER


def archive_sources(files):
    target = BytesIO()
    with ZipFile(target, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for name, raw in sorted(files.items()):
            parse(raw, filename=name, feature_version=(3, 12))
            info = ZipInfo(name)
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw, compress_type=ZIP_DEFLATED, compresslevel=9)
    return target.getvalue()


def disclosed_cases(disclosed):
    require(disclosed.name == DISCLOSED, "disclosed smoke requires its original public trial")
    packet = json.loads(checked(disclosed / "Packet/Packet.json", DISCLOSED_FREEZE))
    build = json.loads(checked(disclosed / "Packet/Build.json", DISCLOSED_BUILD))
    native = json.loads(checked(disclosed / "NativeResult/Result.json", DISCLOSED_RESULT))
    require(packet["native_build"] == BUILD and native["build"] == BUILD and native["passed"] is True
            and native["packet_sha256"] == DISCLOSED_FREEZE and native["build_sha256"] == DISCLOSED_BUILD
            and native["distinct_processes"] == 6 and native["heldout_cases"] == 0,
            "disclosed smoke does not own the two bracketed control designs")
    saved = json.loads(checked(ROOT / "re/solidworks/measurements/2026/SharedLinearPatternDefaults01.json", DEFAULT_SMOKE))
    models = build["model_cases"]
    require(set(models) == set(saved["cases"]) and len(models) == 2, "missing disclosed smoke case")
    return tuple((models[name]["original"]["modeled_input"], saved["cases"][name]) for name in sorted(models))


def smoke(python, entry, work, cases, *, tracing):
    discovered = {entry.relative_to(work).as_posix()}
    recorded, bad_request = [], None

    def execute(mode, payload):
        if tracing:
            task = run((str(python), "-I", "-B", "-c", TRACE, str(entry), str(work), mode),
                       cwd=work, input=payload, capture_output=True, timeout=90, check=False)
            require(task.returncode == 0, "disclosed trace process refused\n" + task.stderr.decode())
            discovered.update(Path(name).relative_to(work).as_posix() for name in json.loads(task.stderr))
        else:
            task = invoke(python, entry, mode, payload, work)
            require(task.returncode == 0 and not task.stderr, "packaged disclosed process refused\n" + task.stderr.decode())
        return json.loads(task.stdout)

    for model, expected in cases:
        request = check_request(execute("--bridge", encode(model)))
        require(request["target"] == {"PathName": model["seed"]["path"], "SavedAt": model["seed"]["epoch"]},
                "disclosed bridge changed actual target provenance")
        neutral = encode(request)
        first, second = (check_product(execute("--emit", neutral)) for _ in range(2))
        value, _ = first
        require(first == second and value["sha256"] == expected["complete_file_sha256"]
                and value["bytes"] == expected["complete_bytes"]
                and value["streams"] == {key: stream["sha256"] for key, stream in expected["streams"].items()},
                "disclosed source closure did not reproduce the exact independently derived default")
        recorded.append({"sha256": value["sha256"], "bytes": value["bytes"], "stream_count": len(value["streams"]),
                         "root_count": value["root_count"], "typed_replays": value["typed_replays"]})
        if bad_request is None:
            bad_request = deepcopy(request)
            bad_request["document"]["metadata"]["unknown-presentation"] = []
    bad = invoke(python, entry, "--emit", encode(bad_request), work)
    require(bad.returncode != 0 and not bad.stdout and b"ordinary neutral part name" in bad.stderr,
            "invalid disclosed metadata reached the archive writer")
    return recorded, discovered


def freeze(prior, disclosed, destination, guest_python, local_python):
    require(prior.name == PRIOR_TRIAL and destination.name == TRIAL and destination.parent == prior.parent
            and not destination.exists(), "choose the unused sibling parity packet")
    legacy = json.loads(checked(prior / "Packet/Freeze.json", PRIOR_FREEZE))
    pinned_result(checked(prior / "Public/Result.json", PRIOR_RESULT))
    guest_root = PureWindowsPath(legacy["guest_root"]).with_name(TRIAL)
    require(guest_root.is_absolute() and guest_root.drive == r"\\Mac\Home" and guest_python.is_absolute()
            and guest_python.drive == "C:" and guest_python.name.casefold() == "python.exe",
            "unexpected guest share or Python entrypoint")
    head = git("rev-parse", "HEAD").decode().strip()
    require(git("rev-parse", f"{head}:src").decode().strip() == SDK_TREE
            and git("rev-parse", f"{SDK_REVISION}:src").decode().strip() == SDK_TREE
            and not git("diff", "--name-only", SDK_REVISION, "--", "src"),
            "the candidate SDK differs from its fixed revision")
    interpreter = check_output((str(local_python), "-I", "-B", "-c",
                                "import sys; assert sys.version_info[:2] == (3,12); print(sys.version.split()[0])")).decode().strip()
    cases = disclosed_cases(disclosed)
    sources = tracked_sources(head)
    with TemporaryDirectory(prefix="KitPatternDefaultParity-") as work:
        work = Path(work).resolve()
        trace_root = work / "Trace"
        outputs, needed = smoke(local_python, materialize(sources, trace_root), trace_root, cases, tracing=True)
        needed.update(name for name in GUARD_PACKAGES if name in sources)
        require({WORKER, GUARD, TOOL_PATH + "/PatternParityPacket.py"} <= needed <= sources.keys(),
                "disclosed imports escaped the committed code inventory")
        files = {name: sources[name] for name in needed}
        payload = archive_sources(files)
        members = {name: identity(raw) for name, raw in files.items()}
        final_root = work / "Frozen"
        verified, _ = smoke(local_python, unpack_sources(payload, members, final_root), final_root, cases, tracing=False)
        require(verified == outputs, "source archive differs from traced disclosed generation")
    packet = destination / "Packet"
    (packet / "Tools").mkdir(parents=True, exist_ok=False)
    files = {"Source.zip": payload, **{f"Tools/{leaf}": sources[f"{TOOL_PATH}/{leaf}"]
                                      for leaf in ("PatternParityPacket.py", "RunPatternDefaultParity.py")}}
    for name, raw in files.items():
        exclusive(packet / name, raw)
    manifest = {
        "schema": SCHEMA, "sdk_revision": SDK_REVISION, "sdk_src_tree": SDK_TREE, "tool_revision": head,
        "prior_freeze_sha256": PRIOR_FREEZE, "prior_result_sha256": PRIOR_RESULT, "disclosed_default_sha256": DEFAULT_SMOKE,
        "native_build": BUILD, "guest_root": str(guest_root), "slots": list(SLOTS), "writer_worker": WORKER,
        "host_smoke": {"python": interpreter, "disclosed_cases": outputs, "traced_processes": 7,
                       "packaged_processes": 7, "native_processes_started": 0, "private_inputs_read": 0},
        "source_members": members, "packet_files": {name: identity(raw) for name, raw in files.items()},
    }
    pin = digest(encode(manifest))
    exclusive(packet / "Manifest.json", encode(manifest))
    require(verified_packet(packet, pin) == manifest, "prepared packet no longer verifies")
    entry = guest_root / "Packet" / "Tools" / "RunPatternDefaultParity.py"
    argv = ["prlctl", "exec", "Windows 11", "--current-user", str(guest_python), "-E", "-B",
            str(entry), "--pin", pin]
    recipe = {"packet_sha256": pin, "writer_source_count": len(members), "source_zip_sha256": digest(payload),
              "private_inputs_read": 0, "guest_argv": argv}
    exclusive(destination / "Recipe.json", encode(recipe))
    print(json.dumps(recipe, sort_keys=True), flush=True)


def main():
    parser = ArgumentParser(description="Freeze a pure Python default pattern byte comparison for the Windows custodian")
    parser.add_argument("--prior", required=True, type=Path)
    parser.add_argument("--disclosed", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--local-python312", required=True, type=Path)
    parser.add_argument("--guest-python", required=True, type=PureWindowsPath)
    args = parser.parse_args()
    freeze(args.prior.resolve(strict=True), args.disclosed.resolve(strict=True), args.output.resolve(),
           args.guest_python, args.local_python312.resolve(strict=True))


if __name__ == "__main__":
    main()
