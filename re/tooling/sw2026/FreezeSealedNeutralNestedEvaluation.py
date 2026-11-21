from argparse import ArgumentParser
from io import BytesIO
from pathlib import Path, PurePosixPath
from shutil import copyfile
from subprocess import check_output, run
from tarfile import open as open_tar
import json
import sys

from AuthorCurves import digest, require, write_json
from FreezeSealedNestedEvaluation import CHECKOUT, SCHEMA, SOURCE_LOCK, SOURCE_PHASE, TOOLS, guest_locator
from NestedAssemblySourcePlan import ORACLE, checked
from SealedNeutralNestedProfile import EVIDENCE_FILES, EVIDENCE_ROLES, PROFILE, WORKER, read_evidence


ROOT = Path(__file__).resolve().parent
AUTHOR_FIXTURE = "tests/Convert/Solidworks/Research/Construction/Part/MakePlainDoc.py"
WORKER_HELPERS = tuple("re/tooling/sw2026/" + name for name in ("AuthorNestedRectangle.py", "SdkNativeRoundTrips.py"))


def git(*args):
    return check_output(("git", *args), cwd=CHECKOUT)


def code_snapshot(output, revision, tree):
    code = output / "CodeRoot"
    code.mkdir()
    hashes = {}

    def store(relative, data):
        path = code / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(data)
        hashes[relative] = digest(path)

    archive = git("archive", revision, "--", "src")
    with open_tar(fileobj=BytesIO(archive), mode="r:") as source:
        for entry in source:
            if PurePosixPath(entry.name).suffix != ".py":
                continue
            require(entry.isfile() and PurePosixPath(entry.name).parts[0] == "src", "invalid committed SDK file")
            with source.extractfile(entry) as stream:
                store(entry.name, stream.read())
    parents = [str(path / "__init__.py") for path in PurePosixPath(AUTHOR_FIXTURE).parents if path.parts]
    present = git("ls-tree", "-r", "--name-only", revision, "--", *parents).decode().splitlines()
    for name in (WORKER, *WORKER_HELPERS, AUTHOR_FIXTURE, *present):
        store(name, git("show", f"{revision}:{name}"))
    manifest = output / "CodeManifest.json"
    write_json(manifest, {"schema": "kit.sw2026.frozen-nested-writer-code.v1", "writer_revision": revision,
                          "sdk_tree": tree, "files_sha256": hashes})
    return digest(manifest)


def prepare(args):
    output = args.output.resolve()
    require(not output.exists() and output.parent.is_dir() and not output.is_relative_to(CHECKOUT),
            "choose an unused shared evaluation packet directory outside the checkout")
    revision = git("rev-parse", "--verify", args.revision + "^{commit}").decode().strip()
    tree = git("rev-parse", revision + ":src").decode().strip()
    require(revision == args.revision, "provide the exact disclosed writer revision")
    source_lock_file = checked(CHECKOUT / "re/solidworks/v2026/heldout/NestedAssemblySourceLock01.json", SOURCE_LOCK, CHECKOUT)
    source_phase_file = checked(args.source_phase, SOURCE_PHASE)
    source_lock = json.loads(source_lock_file.read_bytes())
    require(source_lock["passed"] and source_lock["heldout_payloads_read"] == 0
            and all(row["heldout_source_locked"] for row in source_lock["slots"]),
            "both source slots must have been locked before writer exposure")
    source_guest = guest_locator(args.source_phase_guest, "SealedPhases.json")
    private_base = guest_locator(args.guest_private_base, fixed=True)
    disclosed_results = guest_locator(args.disclosed_results_guest, "Results")
    runner = git("rev-parse", "HEAD").decode().strip()
    paths = [f"re/tooling/sw2026/{name}" for name in TOOLS]
    require(not git("diff", "--name-only", runner, "--", *paths),
            "commit the public evaluator sources before freezing")

    output.mkdir()
    copyfile(source_lock_file, output / "SourceLock.json")
    copyfile(source_phase_file, output / "SourcePhase.json")
    proofs = {}
    for role, source in zip(EVIDENCE_ROLES, (args.first, args.repeated), strict=True):
        source = source.resolve(strict=True)
        proof = output / role
        proof.mkdir()
        files = {}
        for name in EVIDENCE_FILES:
            original = source / ("Inspection/Result.json" if name == "Result.json" else name)
            require(original.is_file() and not original.is_symlink(), "disclosed native evidence file is unavailable")
            copyfile(original, proof / name)
            files[name] = digest(proof / name)
        read_evidence(proof, files, revision, tree, SOURCE_LOCK)
        proofs[role] = files

    tools = output / "Tools"
    tools.mkdir()
    tool_hashes = {}
    for name, path in zip(TOOLS, paths, strict=True):
        destination = tools / name
        destination.write_bytes(git("show", f"{runner}:{path}"))
        tool_hashes[name] = digest(destination)
    code_pin = code_snapshot(output, revision, tree)
    packet = output / "Evaluation.json"
    write_json(packet, {"schema": SCHEMA, "writer_profile": PROFILE, "oracle_sha256": ORACLE,
                        "writer_revision": revision, "code_manifest_sha256": code_pin, "tools_sha256": tool_hashes,
                        "source_lock_sha256": SOURCE_LOCK, "source_phase_sha256": SOURCE_PHASE, "source_phase_guest": source_guest,
                        "guest_private_base": private_base, "disclosed_results_guest": disclosed_results, "disclosed_evidence": proofs,
                        "host_heldout_payloads_read": 0, "sealed_results": True, "native_acceptance": False})
    pin = digest(packet)
    result = run((sys.executable, "-B", str(tools / "RunSealedNestedEvaluation.py"), "verify", str(packet),
                  "--packet-sha256", pin), capture_output=True, text=True, timeout=150)
    require(result.returncode == 0 and not result.stderr and json.loads(result.stdout)["verified_packet"] == pin,
            "the sealed neutral evaluation packet did not pass public preflight")
    return {"packet_sha256": pin, "code_manifest_sha256": code_pin, "writer_revision": revision,
            "evaluator_revision": runner, "host_heldout_payloads_read": 0, "native_processes_started": 0}


if __name__ == "__main__":
    parser = ArgumentParser()
    for name in ("first", "repeated", "source-phase", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("revision", "source-phase-guest", "guest-private-base", "disclosed-results-guest"):
        parser.add_argument("--" + name, required=True)
    print(json.dumps(prepare(parser.parse_args()), sort_keys=True))
