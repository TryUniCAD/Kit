from argparse import ArgumentParser
from ast import parse
from io import BytesIO
from pathlib import Path, PureWindowsPath
from subprocess import check_output
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[6]
PARITY_HELPER = HERE.parent.parent / "default_parity/PatternParityPacket.py"
sys.path[:0] = [str(HERE.parent), str(PARITY_HELPER.parent)]

from PatternParityPacket import (
    DEFAULT_SMOKE, SLOTS, TRIAL as BASE_TRIAL, checked, check_product, digest, encode, exclusive,
    identity, invoke, require, safe_python, verified_packet,
)
from PublicPatternPacket import (
    BASE_MANIFEST, BASE_RESULT, BASE_REVISION, BASE_ZIP, SCHEMA, SDK_REVISION, SDK_TREE, SOURCE_LOCK,
    TRIAL, WORKER, frozen_slots, install_overlay, verified,
)


FIXTURE = "re/tooling/sw2026/linear_pattern/neutral/PublicPatternWriteInputs.json"
FIXTURE_SHA = "5784abcd6ccc6e93feb88463333b5668bf4fd12f18fa2bde5efbfcc1ccabcdef"
PUBLIC_IMPORTS = ("src/interchange/document/Models/DocumentProvenance.py",)


def git(*args):
    return check_output(("git", *args), cwd=ROOT)


def tracked(revision, name):
    entry, path = git("ls-tree", revision, name).decode().rstrip("\n").split("\t", 1)
    mode, kind, _ = entry.split()
    require(path == name and kind == "blob" and mode in ("100644", "100755"), "frozen source contains a link")
    safe_python(path)
    raw = git("show", f"{revision}:{path}")
    parse(raw, filename=name, feature_version=(3, 12))
    return raw


def overlay_bytes(head):
    names = git("diff", "--name-status", "-z", BASE_REVISION, SDK_REVISION, "--", "src").decode().rstrip("\0").split("\0")
    require(len(names) % 2 == 0 and all(change in ("A", "M") for change in names[::2]),
            "current SDK needs an unmodeled source removal or rename")
    files = {name: tracked(SDK_REVISION, name) for name in (*names[1::2], *PUBLIC_IMPORTS)}
    files[WORKER] = tracked(head, WORKER)
    target = BytesIO()
    with ZipFile(target, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for name, value in sorted(files.items()):
            row = ZipInfo(name)
            row.external_attr = 0o100644 << 16
            archive.writestr(row, value, compress_type=ZIP_DEFLATED, compresslevel=9)
    return target.getvalue(), {name: identity(raw) for name, raw in sorted(files.items())}


def smoke(entry, work, python):
    cases = json.loads(checked(ROOT / FIXTURE, FIXTURE_SHA))
    defaults_file = ROOT / "re/solidworks/measurements/2026/SharedLinearPatternDefaults01.json"
    defaults = json.loads(checked(defaults_file, DEFAULT_SMOKE))["cases"]
    results = []
    for name, row in sorted(cases.items()):
        request = encode({key: row[key] for key in ("document", "target")})
        task = invoke(python, entry, "--emit", request, work)
        require(task.returncode == 0 and not task.stderr, "disclosed public SDK writer refused\n" + task.stderr.decode())
        product, _ = check_product(json.loads(task.stdout))
        prior = defaults[name]
        require(product["sha256"] == prior["complete_file_sha256"] and product["bytes"] == prior["complete_bytes"]
                and product["streams"] == {stream: pin["sha256"] for stream, pin in prior["streams"].items()},
                "the two public stream routes did not reproduce their independently modeled disclosed output")
        results.append({key: product[key] for key in ("sha256", "bytes", "typed_replays", "runtime_reads")})
    require(len(results) == 2 and results[0]["sha256"] != results[1]["sha256"], "both disclosed profiles are required")
    return results


def freeze(prior, output, guest_python, local_python):
    require(prior.name == BASE_TRIAL and output.name == TRIAL and output.parent == prior.parent
            and not output.exists(), "choose an unused public parity sibling packet")
    old = prior / "Packet"
    base = verified_packet(old, BASE_MANIFEST)
    slots = frozen_slots(checked(prior / "Public" / "Result.json", BASE_RESULT))
    guest_root = PureWindowsPath(base["guest_root"]).with_name(TRIAL)
    require(guest_root.drive.casefold() == r"\\mac\home" and guest_root.parent.name == "Oracle121Takeover"
            and guest_python.drive.upper() == "C:" and guest_python.is_absolute()
            and guest_python.name.casefold() == "python.exe", "unexpected guest root or Python")
    head = git("rev-parse", "HEAD").decode().strip()
    require(git("rev-parse", f"{head}:src").decode().strip() == SDK_TREE
            and not git("diff", "--name-only", SDK_REVISION, "--", "src"), "exact integrated SDK required")
    python_version = check_output((str(local_python), "-I", "-B", "-c",
                                   "import sys; assert sys.version_info[:2] == (3,12); print(sys.version.split()[0])")).decode().strip()
    overlay, members = overlay_bytes(head)
    with TemporaryDirectory(prefix="KitPublicPatternParity-") as directory:
        work = Path(directory).resolve()
        entry = install_overlay(old, base, overlay, members, work)
        cases = smoke(entry, work, local_python)
    packet = output / "Packet"
    (packet / "Tools").mkdir(parents=True, exist_ok=False)
    files = {"Overlay.zip": overlay}
    for path in (PARITY_HELPER, HERE.parent / "PublicPatternPacket.py", HERE.parent / "RunPublicPatternParity.py"):
        name = path.relative_to(ROOT).as_posix()
        files["Tools/" + path.name] = tracked(head, name)
        require(path.read_bytes() == files["Tools/" + path.name], "working tool differs from committed code")
        if path == PARITY_HELPER:
            checked(old / "Tools" / path.name, identity(files["Tools/" + path.name]))
    for name, raw in files.items():
        exclusive(packet / name, raw)
    manifest = {
        "schema": SCHEMA, "tool_revision": head, "sdk_revision": SDK_REVISION, "sdk_source_tree": SDK_TREE,
        "guest_root": str(guest_root), "parity_manifest_sha256": BASE_MANIFEST, "parity_result_sha256": BASE_RESULT,
        "base_source_zip_sha256": BASE_ZIP, "source_lock_sha256": SOURCE_LOCK, "slots": slots,
        "overlay_members": members, "files": {name: identity(raw) for name, raw in files.items()},
        "host_smoke": {"python": python_version, "guarded_processes": 2, "public_write_calls": 4,
                       "strict_stream_reads": 2, "private_inputs_read": 0, "native_processes_started": 0, "cases": cases},
    }
    raw = encode(manifest)
    pin = digest(raw)
    exclusive(packet / "Manifest.json", raw)
    require(verified(packet, pin) == manifest and tuple(manifest["slots"]) == SLOTS, "staged overlay did not reverify")
    script = guest_root / "Packet" / "Tools" / "RunPublicPatternParity.py"
    argv = ["prlctl", "exec", "Windows 11", "--current-user", str(guest_python), "-E", "-B", str(script), "--pin", pin]
    recipe = {"packet_sha256": pin, "overlay_zip_sha256": digest(overlay), "overlay_members": len(members),
              "guest_argv": argv, "terminal_receipt": str(guest_root / "Public" / "Result.json")}
    exclusive(output / "Recipe.json", encode(recipe))
    print(json.dumps(recipe, sort_keys=True))


def main():
    parser = ArgumentParser(description="Freeze an exact public SDK overlay on the existing protected pattern parity code")
    parser.add_argument("--prior", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--guest-python", required=True, type=PureWindowsPath)
    parser.add_argument("--local-python312", required=True, type=Path)
    args = parser.parse_args()
    freeze(args.prior.resolve(strict=True), args.output.resolve(), args.guest_python, args.local_python312.resolve(strict=True))


if __name__ == "__main__":
    main()
