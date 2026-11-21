import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from NativeAcceptance.Availability import ApiStatus
from NativeAcceptance.CompareFile import CompareFile
from NativeAcceptance.Records import Endpoint, FileHash, WriteJson


def EnableFusion(root):
    if sys.platform == "darwin":
        base = Path.home() / "Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns"
    elif sys.platform == "win32" and os.environ.get("APPDATA"):
        base = Path(os.environ["APPDATA"]) / "Autodesk/Autodesk Fusion 360/API/AddIns"
    else:
        raise ValueError("Fusion API verification requires macOS or Windows")
    endpoint = Endpoint()
    endpoint.mkdir(parents=True, mode=0o700, exist_ok=True)
    if os.name == "posix" and (endpoint.is_symlink() or endpoint.stat().st_mode & 0o077):
        raise ValueError("Fusion verification endpoint must be private to its owner")
    target = base / "KitVerify"
    source = root / "re/automation/NativeAcceptance/KitVerify"
    target.mkdir(parents=True, exist_ok=True)
    for name in ("KitVerify.py", "KitVerify.manifest"):
        destination = target / name
        if destination.exists() and destination.read_bytes() != (source / name).read_bytes():
            raise ValueError(f"existing add-in differs; remove or review {destination} before installation")
        shutil.copyfile(source / name, destination)
    sources = {
        str(path.relative_to(root)): FileHash(path)
        for path in sorted((root / "re/automation/NativeAcceptance").rglob("*.py"))
    }
    revision = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True, timeout=15).stdout.strip()
    WriteJson(endpoint / "config.json", {"version": 1, "source_root": str(root), "source_revision": revision, "sources": sources})
    return {"status": "enable_required", "addin": str(target), "action": "In Fusion Scripts and Add-Ins enable KitVerify and Run on Startup, then close Fusion and rerun the decoding command"}


def MainApi():
    parser = argparse.ArgumentParser(description="Detect or enable the local API, or compare saved measurements without native acceptance")
    parser.add_argument("operation", choices=("status", "enable", "compare"))
    parser.add_argument("application", choices=("solidworks", "fusion"))
    parser.add_argument("--document", type=Path)
    parser.add_argument("--measurement", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    paths = (args.document, args.measurement, args.output)
    if args.operation == "compare" and not all(paths):
        parser.error("compare requires --document, --measurement and --output")
    if args.operation != "compare" and any(paths):
        parser.error("comparison paths are only valid with compare")
    try:
        root = Path(__file__).resolve().parents[3]
        if args.operation == "compare":
            sys.path.insert(0, str(root / "src"))
            result = CompareFile(args.application, args.document, args.measurement, args.output)
        else:
            result = EnableFusion(root) if args.operation == "enable" and args.application == "fusion" else ApiStatus(args.application)
        print(json.dumps(result, sort_keys=True))
        if args.operation == "compare":
            return 0 if result["status"] == "passed" else 5
        return 0 if result["status"] == "available" else 4
    except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError, RecursionError, OverflowError, subprocess.SubprocessError) as error:
        parser.exit(1, f"native API setup failed: {error}\n")


if __name__ == "__main__":
    sys.exit(MainApi())
