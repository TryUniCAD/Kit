from argparse import ArgumentParser
from ast import parse
from pathlib import Path, PureWindowsPath
from subprocess import check_output
from tempfile import TemporaryDirectory
import json
import os
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[6]
TOOL_PATH = HERE.parent.relative_to(ROOT).as_posix()
PARITY_HELPER = HERE.parent.parent / "default_parity/PatternParityPacket.py"
sys.path[:0] = [str(HERE.parent), str(PARITY_HELPER.parent)]

from NativePatternPacket import ORACLE, PARITY_MANIFEST, PARITY_RESULT, ROLES, SCHEMA, SOURCE_LOCK, TOOLS, TRIAL, divergent, verified
from PatternLocatorLease import install, lease_row, paths, restore
from PatternParityPacket import BUILD, PRIOR_FREEZE, PRIOR_RESULT, SDK_REVISION, SDK_TREE, TRIAL as PARITY_TRIAL, checked, digest, encode, exclusive, identity, require


PARITY_TOOL_REVISION = "22eb1a529649e82c2f2ca5927de09b3f29552658"


def git(*args):
    return check_output(("git", *args), cwd=ROOT)


def tracked(revision, path):
    name = path.relative_to(ROOT).as_posix()
    entry, selected = git("ls-tree", revision, name).decode().rstrip("\n").split("\t", 1)
    mode, kind, _ = entry.split()
    require(selected == name and kind == "blob" and mode == "100644" and path.suffix == ".py",
            "staged entry must be the exact regular tracked Python file")
    raw = git("show", f"{revision}:{name}")
    require(raw == path.read_bytes(), "local tooling bytes differ from the committed packet")
    parse(raw, filename=name, feature_version=(3, 12))
    return raw


def prove_lease():
    original, candidate, note = b"prior owned probe", b"new owned probe", "0" * 64
    prior = digest(original)
    with TemporaryDirectory(prefix="KitPatternLocatorLease-") as directory:
        home = Path(directory)
        locator = home / "SharedName.SLDPRT"
        for position in ("complete", "before-install", "before-restore"):
            folder = home / position
            folder.mkdir()
            journal, parked, staged, observed = paths(folder)
            if position == "complete":
                exclusive(locator, original)
                install(folder, locator, prior, candidate, note)
                require(checked(locator, digest(candidate)) == candidate and checked(parked, prior) == original,
                        "exact working locators did not preserve both artifacts")
            else:
                exclusive(journal, encode(lease_row(locator, prior, candidate, note)))
                os.rename(locator, parked)
                exclusive(staged if position == "before-install" else observed, candidate)
            restore(folder, locator, prior, candidate, note)
            restore(folder, locator, prior, candidate, note)
            require(checked(locator, prior) == original and not parked.exists(),
                    "normal or interrupted file handoff failed to restore the prior digest")
            remaining = staged if position == "before-install" else observed
            require(checked(remaining, digest(candidate)) == candidate, "new owned bytes were not retained")
    return {"synthetic_locator_states_restored": 3, "native_launches": 0, "protected_files_read": 0}


def freeze(prior_result, output, guest_root, guest_python):
    require(prior_result.name == "Result.json" and prior_result.parent.name == "Public"
            and prior_result.parent.parent.name == PARITY_TRIAL
            and output.parent == prior_result.parents[2] and output.name == TRIAL and not output.exists(),
            "choose the unused sibling of the existing redacted parity receipt")
    require(guest_root.is_absolute() and guest_root.drive.casefold() == r"\\mac\home"
            and guest_root.parent.name == "Oracle121Takeover" and guest_root.name == TRIAL
            and guest_python.is_absolute() and guest_python.drive.upper() == "C:"
            and guest_python.name.casefold() == "python.exe", "unexpected guest root or Python executable locator")
    scope = divergent(checked(prior_result, PARITY_RESULT))
    head = git("rev-parse", "HEAD").decode().strip()
    require(git("rev-parse", f"{head}:src").decode().strip() == SDK_TREE and not git("diff", "--name-only", SDK_REVISION, "--", "src")
            and tracked(head, HERE) == HERE.read_bytes(), "parity SDK or freezer source changed")
    files = {"Tools/" + name: tracked(PARITY_TOOL_REVISION, PARITY_HELPER) if name == PARITY_HELPER.name
             else tracked(head, HERE.parent / name) for name in sorted(TOOLS)}
    checks = prove_lease()
    packet = output / "Packet"
    (packet / "Tools").mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        exclusive(packet / name, data)
    manifest = {
        "schema": SCHEMA, "tool_revision": head, "sdk_revision": SDK_REVISION,
        "guest_root": str(guest_root), "native_build": BUILD, "oracle_sha256": ORACLE, "scope": scope,
        "parity_manifest_sha256": PARITY_MANIFEST, "parity_result_sha256": PARITY_RESULT,
        "prior_result_sha256": PRIOR_RESULT, "prior_freeze_sha256": PRIOR_FREEZE, "source_lock_sha256": SOURCE_LOCK,
        "expected_distinct_processes": 11, "phase_roles": list(ROLES), "host_checks": checks,
        "files": {name: identity(raw) for name, raw in files.items()},
    }
    raw = encode(manifest)
    pin = digest(raw)
    exclusive(packet / "Manifest.json", raw)
    require(verified(packet, pin) == manifest, "fresh native packet does not match its freeze")
    script = guest_root / "Packet" / "Tools" / "RunPatternDefaultNative.py"
    argv = ["prlctl", "exec", "Windows 11", "--current-user", str(guest_python), "-E", "-B", str(script), "--pin", pin]
    recipe = {"packet_sha256": pin, "guest_argv": argv, "guest_recovery_argv": [*argv, "--restore-only"],
              "terminal_receipt": str(guest_root / "Public" / "Result.json"), **checks}
    exclusive(output / "Recipe.json", encode(recipe))
    print(json.dumps(recipe, sort_keys=True))


def main():
    parser = ArgumentParser(description="Freeze a one-slot native comparison from its previously redacted parity result")
    parser.add_argument("--prior-result", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--guest-root", required=True, type=PureWindowsPath)
    parser.add_argument("--guest-python", required=True, type=PureWindowsPath)
    args = parser.parse_args()
    freeze(args.prior_result.resolve(strict=True), args.output.resolve(), args.guest_root, args.guest_python)


if __name__ == "__main__":
    main()
