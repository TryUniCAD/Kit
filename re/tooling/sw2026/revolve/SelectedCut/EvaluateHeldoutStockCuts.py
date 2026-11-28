from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
from subprocess import check_output, run
import sys
from tarfile import TarInfo, open as open_tar
from time import time
from traceback import format_exc

HERE = Path(__file__).resolve()
TOOLS = "re/tooling/sw2026/"
SELECTED = TOOLS + "revolve/SelectedCut/"
THIS = SELECTED + HERE.name
SCHEMA = "kit.sw2026.selected-revolve-heldout-evaluation.v1"
LOCK = "re/solidworks/measurements/2026/RevolveCutHeldoutSourceLock01.json"
LOCK_SHA = "67c1aeca25817846925f18e5b6b7b9319bdba216835e685988961e0db8832f68"
LOCK_REVISION = "642b20cc65d14262ecc1e78e478af5ab48ca59b0"
FORWARD_BUILDER = "8953acb4be7f72230ea71de1935f3392df0378e9"
BUILDER = "877b49b1e31eecd671bd1107455d8d70e9b93b38"
DISCLOSURE = "re/solidworks/measurements/2026/SdkScopedRevolvePrincipalNative01.json"
DISCLOSURE_SHA = "66300aa22b70a44f0b70e3e45420b426827ed8ea149a8316199bb7ee9f200258"
REVERSE_DISCLOSURE = "re/solidworks/measurements/2026/SdkScopedRevolveReverseNative01.json"
REVERSE_DISCLOSURE_SHA = "b310fcd0e0b25305aa2e97b2c9451673b174eac5c0376eb7cd55f4916a0ac292"
PROBE = "re/solidworks/measurements/2026/SdkScopedRevolvePrincipalPacket01.json"
PROBE_SHA = "fa54b00919aec9116c36b0d16a2a447d59621a2e20118f67bb0a9c1eaea380e0"
PROBE_SPEC = SELECTED + "StockCutPrincipalDisclosures01.json"
REVERSE_PROBE = "re/solidworks/measurements/2026/SdkScopedRevolveReversePacket01.json"
REVERSE_PROBE_SHA = "36380d1259581b8594f977ca3970239cd7c2bfdb3d06811dc97afddee4bbe59d"
REVERSE_PROBE_SPEC = SELECTED + "StockCutReverseDisclosures02.json"
DISCLOSED_PACKETS = (
    (PROBE, PROBE_SHA, PROBE_SPEC, "ScopedRevolveFrontier02"),
    (REVERSE_PROBE, REVERSE_PROBE_SHA, REVERSE_PROBE_SPEC, "ScopedRevolveReverse03"),
)
PREFIX = PureWindowsPath(r"C:\KitSdkCandidates")
SPEC = PREFIX / "RevolveCutHeldout01Author" / "Spec.json"
ORIGINALS = PREFIX / "RevolveCutHeldout01"
GUEST_SHARE = PureWindowsPath(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover")
CONTROL = GUEST_SHARE / "RevolveCutSelector01" / "Control" / "RevolveFull.SLDPRT"
TOOL_NAMES = (
    "AuthorRevolveFamilies.py", "RevolveFamilyModel.py", "AuthorRevolveSources.py",
    "AuthorCurves.py", "ComparePerpendicularRuntimes.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py",
)


def digest(data):
    return sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked(path, pin):
    require(path.is_file() and not path.is_symlink(), "expected an intact pinned file")
    raw = path.read_bytes()
    require(digest(raw) == pin, "file differs from the frozen digest: " + path.name)
    return raw


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def publish(path, raw):
    with path.open("xb") as stream:
        stream.write(raw)
    return digest(raw)


def freeze(output):
    root = HERE.parents[5]
    require(output.is_absolute() and not output.exists() and not output.is_relative_to(root)
            and output.name.startswith("ScopedRevolveHeldoutEval")
            and output.name.removeprefix("ScopedRevolveHeldoutEval").isdigit(),
            "choose a new external evaluation packet")

    def git(*args):
        return check_output(("git", *args), cwd=root)

    def committed(name):
        return git("show", f"{revision}:{name}")

    revision = git("rev-parse", "HEAD").decode().strip()
    for ancestor in (LOCK_REVISION, FORWARD_BUILDER, BUILDER):
        git("merge-base", "--is-ancestor", ancestor, revision)
    git("merge-base", "--is-ancestor", LOCK_REVISION, FORWARD_BUILDER)
    lock = checked(root / LOCK, LOCK_SHA)
    disclosure = checked(root / DISCLOSURE, DISCLOSURE_SHA)
    reverse_disclosure = checked(root / REVERSE_DISCLOSURE, REVERSE_DISCLOSURE_SHA)
    require(lock == committed(LOCK) and disclosure == committed(DISCLOSURE)
            and reverse_disclosure == committed(REVERSE_DISCLOSURE)
            and json.loads(disclosure)["passed"] and json.loads(disclosure)["controls_healthy"]
            and json.loads(reverse_disclosure)["passed"] and json.loads(reverse_disclosure)["controls_healthy"]
            and json.loads(lock)["finished_at"] < int(git("show", "-s", "--format=%ct", FORWARD_BUILDER)),
            "the exact disclosed result and earlier independent native lock are required")
    children = git("ls-tree", "-r", "--name-only", revision, TOOLS + "revolve").decode().splitlines()
    paths = {LOCK, DISCLOSURE, REVERSE_DISCLOSURE, PROBE, PROBE_SPEC, REVERSE_PROBE, REVERSE_PROBE_SPEC,
             *(name for name in children if name.endswith(".py")),
             *(TOOLS + name for name in TOOL_NAMES)}
    exact = {name: committed(name) for name in sorted(paths)}
    builder = SELECTED + "BuildStockCutSelector.py"
    require(exact[THIS] == HERE.read_bytes()
            and exact[builder] == git("show", f"{BUILDER}:{builder}")
            and all(digest(exact[probe]) == probe_sha
                    and digest(exact[spec_path]) == json.loads(exact[probe])["files"]["ModelSpecs.json"]
                    for probe, probe_sha, spec_path, _ in DISCLOSED_PACKETS)
            and not git("diff", "--name-only", revision, "--", "src", *paths),
            "construction and evaluation tools must match the committed revision")

    packed = BytesIO()
    source_tar = git("archive", "--format=tar", revision, "src")
    with open_tar(fileobj=BytesIO(source_tar), mode="r:") as source, open_tar(fileobj=packed, mode="w:gz") as bundle:
        for member in source:
            require(member.isfile() or member.isdir(), "unsupported source member")
            bundle.addfile(member, source.extractfile(member) if member.isfile() else None)
        for name, raw in exact.items():
            member = TarInfo(name)
            member.size, member.mode = len(raw), 0o644
            bundle.addfile(member, BytesIO(raw))
    code = packed.getvalue()
    manifest = {
        "schema": SCHEMA, "writer_revision": revision,
        "writer_source_tree": git("rev-parse", f"{revision}:src").decode().strip(),
        "generative_method_revision": BUILDER, "forward_method_revision": FORWARD_BUILDER,
        "prewriter_source_lock_revision": LOCK_REVISION,
        "prewriter_source_lock_sha256": LOCK_SHA, "disclosure_sha256": DISCLOSURE_SHA,
        "reverse_disclosure_sha256": REVERSE_DISCLOSURE_SHA,
        "epoch": int(time()), "sealed_inputs_read_by_freeze": 0,
        "packed_code_sha256": digest(code), "files": {name: digest(raw) for name, raw in exact.items()},
        "guest_packet": str(GUEST_SHARE / output.name), "guest_private": str(PREFIX / output.name),
    }
    output.mkdir()
    publish(output / HERE.name, exact[THIS])
    publish(output / "Code.tar.gz", code)
    return {"freeze_sha256": publish(output / "Freeze.json", encode(manifest)),
            "writer_revision": revision, "writer_source_tree": manifest["writer_source_tree"]}


def verify(packet, freeze_pin, *, create=False):
    manifest = json.loads(checked(packet / "Freeze.json", freeze_pin))
    private = Path(manifest["guest_private"])
    target = private / "Code"
    require(os.name == "nt" and manifest["schema"] == SCHEMA
            and private == Path(PREFIX / packet.name)
            and Path(manifest["guest_packet"]).resolve() == packet.resolve()
            and manifest["prewriter_source_lock_sha256"] == LOCK_SHA
            and manifest["prewriter_source_lock_revision"] == LOCK_REVISION
            and manifest["generative_method_revision"] == BUILDER
            and manifest["forward_method_revision"] == FORWARD_BUILDER
            and manifest["disclosure_sha256"] == DISCLOSURE_SHA
            and manifest["reverse_disclosure_sha256"] == REVERSE_DISCLOSURE_SHA
            and manifest["sealed_inputs_read_by_freeze"] == 0
            and digest(HERE.read_bytes()) == manifest["files"][THIS],
            "frozen code, paths or pre-writer custody do not match")
    code = checked(packet / "Code.tar.gz", manifest["packed_code_sha256"])
    with open_tar(fileobj=BytesIO(code), mode="r:gz") as bundle:
        members = bundle.getmembers()
        names = [member.name for member in members]
        require(len(set(name.casefold() for name in names)) == len(names)
                and all((member.isdir() or member.isfile()) and not Path(member.name).is_absolute()
                        and ":" not in member.name and "\\" not in member.name
                        and ".." not in PurePosixPath(member.name).parts
                        and (member.name == "src" or member.name.startswith("src/") or member.name in manifest["files"])
                        for member in members), "unsafe or duplicate member in frozen code")
        if create:
            require(not private.exists(), "the sealed evaluation workspace already exists")
            target.mkdir(parents=True)
            bundle.extractall(target, members=members, filter="data")
        if target.exists():
            require({member.name for member in members if member.isfile()}
                    == {path.relative_to(target).as_posix() for path in target.rglob("*") if path.is_file()},
                    "local code inventory differs from the frozen closure")
        for name, member in ((item.name, item) for item in members if item.isfile()):
            raw = bundle.extractfile(member).read()
            if name in manifest["files"]:
                require(digest(raw) == manifest["files"][name], "packed code digest differs")
            if target.exists():
                require(checked(target / name, digest(raw)) == raw, "local code differs")
    return manifest, private, target


def prepare(packet, pin):
    manifest, private, source = verify(packet, pin, create=True)
    sys.path.insert(0, str(source / SELECTED))
    from CompareStockCutRuntime import compare_host_runtime
    from FreezeScopedRevolveNative import make_candidate, path_for_tool
    from RunScopedRevolveNative import (
        CONTROL as CONTROL_NAME, CONTROL_SHA, LOCK as LOCK_NAME, MODEL, ORACLE_SHA,
        SCHEMA as PACKET_SCHEMA, TOOLS as RUN_TOOLS, path_for, source_lock, validate_specs,
    )

    custody = checked(source / LOCK, LOCK_SHA)
    lock = source_lock(custody)
    host_parity = []
    for probe_path, probe_pin, spec_path, folder in DISCLOSED_PACKETS:
        probe = json.loads(checked(source / probe_path, probe_pin))
        disclosed = validate_specs(json.loads(checked(source / spec_path, probe["files"][MODEL])))
        require(len(disclosed) == 2, "the guest preflight needs both disclosed constructor cases")
        for case in disclosed:
            raw, evidence = make_candidate(case, PureWindowsPath(probe["guest_workspace"]), probe["epoch"])
            prior = probe["construction"][case["name"]]
            baseline = Path(GUEST_SHARE / folder / "Candidates" / path_for(case))
            old_raw = checked(baseline, prior["sha256"])
            require(all(evidence[key] == prior[key] for key in
                        ("zero_runtime_reads", "selector", "active_root_count", "config_counter", "resolved_counter")),
                    "the guest SDK changed the disclosed link or selection")
            host_parity.append(compare_host_runtime(old_raw, raw))
    raw_spec = checked(Path(SPEC), lock["spec_sha256"])
    cases = validate_specs(json.loads(raw_spec))
    require(len(cases) == 2 and {case["plane"] for case in cases} == {"top", "right"}
            and all(case["split"] == "heldout" and case["family"] == "cut"
                    and case["scope"] in ("inner", "outer")
                    for case in cases), "the sealed source is outside the frozen constructor profile")
    workspace = PREFIX / (private.name + "Work")
    require(not Path(workspace).exists(), "the sealed output workspace already exists")
    candidate_packet = private / "CandidatePacket"
    artifacts = {CONTROL_NAME: checked(Path(CONTROL), CONTROL_SHA), MODEL: raw_spec, LOCK_NAME: custody,
                 **{f"Tools/{name}": path_for_tool(name).read_bytes() for name in RUN_TOOLS}}
    with ThreadPoolExecutor(max_workers=4) as pool:
        samples = list(pool.map(lambda case: make_candidate(case, workspace, manifest["epoch"]), (*cases, *cases)))
    proof = {}
    for i, case in enumerate(cases):
        require(samples[i] == samples[i + len(cases)], "isolated construction repeated different bytes")
        raw, item = samples[i]
        artifacts[f"Candidates/{path_for(case)}"] = raw
        proof[case["name"]] = item
    candidate_packet.mkdir()
    for name, raw in artifacts.items():
        target = candidate_packet / name
        target.parent.mkdir(exist_ok=True)
        publish(target, raw)
    record = {
        "schema": PACKET_SCHEMA, "cohort": "heldout", "oracle_sha256": ORACLE_SHA,
        "codec_revision": manifest["writer_revision"], "codec_src_tree": manifest["writer_source_tree"],
        "guest_packet": str(candidate_packet), "guest_workspace": str(workspace),
        "epoch": manifest["epoch"], "generation_workers": len(samples),
        "disclosed_guest_preflight": host_parity, "python_version": sys.version.split()[0],
        "freeze_sha256": pin, "original_native_files_read_by_generation": 0,
        "runtime_reads": 0, "new_heldout_credit": 0, "construction": proof,
        "files": {name: digest(raw) for name, raw in artifacts.items()},
    }
    result = candidate_packet / "Packet.json"
    candidate_pin = publish(result, encode(record))
    verified = run((sys.executable, "-B", str(candidate_packet / "Tools" / RUN_TOOLS[0]),
                    "verify", str(result), "--pin", candidate_pin), capture_output=True, timeout=90)
    require(verified.returncode == 0 and not verified.stderr,
            "frozen candidate verification failed: " + verified.stderr.decode(errors="replace"))
    return {"candidate_packet_sha256": candidate_pin, "generated_cases": len(cases),
            "original_native_files_read_by_generation": 0}


def main(args):
    if args.action == "freeze":
        return freeze(args.packet)
    if args.action == "prepare":
        return prepare(args.packet, args.freeze_pin)
    manifest, private, source = verify(args.packet, args.freeze_pin)
    if args.action == "verify":
        return {"freeze_sha256": args.freeze_pin, "sealed_sources_opened": 0,
                "revision": manifest["writer_revision"]}
    directory = private / "CandidatePacket"
    packet_path = directory / "Packet.json"
    record = json.loads(checked(packet_path, args.candidate_pin))
    require(record["codec_revision"] == manifest["writer_revision"]
            and record["freeze_sha256"] == args.freeze_pin and record["cohort"] == "heldout",
            "candidate packet does not match the frozen method")
    if args.action == "native":
        status = run((sys.executable, "-B", str(directory / "Tools" / "RunScopedRevolveNative.py"),
                      "run", str(packet_path), "--pin", args.candidate_pin), check=False)
        sys.exit(status.returncode)
    sys.path.insert(0, str(source / SELECTED))
    from MatchHeldoutStockCuts import compare
    return compare(private, source, manifest, record, args.native_pin)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("action", choices=("freeze", "verify", "prepare", "native", "compare"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--freeze-pin")
    parser.add_argument("--candidate-pin")
    parser.add_argument("--native-pin")
    options = parser.parse_args()
    try:
        outcome = main(options)
    except Exception as error:
        if options.action == "freeze" or os.name != "nt":
            raise
        detail = format_exc()
        try:
            frozen = json.loads(checked(options.packet / "Freeze.json", options.freeze_pin))
            private = Path(PREFIX / options.packet.name)
            if Path(frozen["guest_private"]) == private and (private / "Code").is_dir():
                publish(private / f"{options.action}-failure.json", encode({"error": detail}))
        except (OSError, ValueError, KeyError):
            pass
        print(json.dumps({"stage": options.action, "error_type": type(error).__name__, "passed": False}))
        sys.exit(1)
    print(json.dumps(outcome, sort_keys=True))
    sys.exit(int(outcome.get("passed", True) is False))
