from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PureWindowsPath


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(packet):
    path = packet / "Packet.json"
    value = json.loads(path.read_bytes())
    if value["schema"] != "kit.sw2026.linear-pattern-source-packet.v1":
        raise ValueError("unexpected linear-pattern source packet")
    for row in value["files"]:
        item = (packet / row["path"]).resolve()
        if not item.is_relative_to(packet.resolve()) or item.stat().st_size != row["bytes"] or digest(item) != row["sha256"]:
            raise ValueError("frozen packet source differs: " + row["path"])
    return digest(path)


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--guest-checkout", required=True)
    parser.add_argument("--guest-disclosed-output", required=True)
    parser.add_argument("--guest-heldout-output", required=True)
    parser.add_argument("--guest-public-progress", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.source_revision):
        raise ValueError("source revision must be the exact published forty-digit commit")
    packet = Path(__file__).resolve().parent
    packet_hash = verify(packet)
    checkout = PureWindowsPath(args.guest_checkout)
    disclosed = PureWindowsPath(args.guest_disclosed_output)
    heldout = PureWindowsPath(args.guest_heldout_output)
    progress = PureWindowsPath(args.guest_public_progress)
    if not all(path.is_absolute() for path in (checkout, disclosed, heldout, progress)):
        raise ValueError("guest paths must be absolute")
    if not heldout.is_relative_to(PureWindowsPath("C:/KitLinearPatternSealed")):
        raise ValueError("held-out raw data must stay in the prescribed guest-private root")
    if args.output.exists() or not args.output.is_absolute() or args.output.resolve().is_relative_to(packet.resolve()):
        raise ValueError("use a new absolute job output directory")
    args.output.mkdir(parents=True, exist_ok=False)
    files = []
    for cohort, output in (("disclosed", disclosed), ("heldout", heldout)):
        value = {"schema": "kit.sw2026.linear-pattern-source-job.v1", "source_revision": args.source_revision, "packet_sha256": packet_hash, "cohort": cohort, "checkout_root": str(checkout), "output": str(output), "public_lock": str(progress / (cohort + "-lock.json"))}
        path = args.output / (cohort + "-job.json")
        write(path, value)
        files.append({"path": path.name, "sha256": digest(path), "bytes": path.stat().st_size})
    write(args.output / "Jobs.json", {"schema": "kit.sw2026.linear-pattern-frozen-source-jobs.v1", "packet_sha256": packet_hash, "source_revision": args.source_revision, "files": files, "native_processes_started": 0, "hidden_inputs_generated_or_read": 0})
    print(json.dumps({"packet_sha256": packet_hash, "jobs_manifest_sha256": digest(args.output / "Jobs.json"), "native_processes_started": 0, "hidden_inputs_generated_or_read": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
