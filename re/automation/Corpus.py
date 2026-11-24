import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from threading import Event, Timer

from Evidence import inspect_evidence


def git_environment():
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_GRAFT_FILE=os.devnull,
        GIT_NO_LAZY_FETCH="1",
        LC_ALL="C",
    )
    return environment


def git(root, *args, input_data=None):
    result = subprocess.run(
        ["git", "--no-replace-objects", "--no-optional-locks", "-C", str(root), *args],
        capture_output=True,
        check=True,
        timeout=120,
        env=git_environment(),
        input=input_data,
    )
    return result.stdout


def start_blob_batch(root, *, stderr=None):
    return subprocess.Popen(
        [
            "git", "--no-replace-objects", "--no-optional-locks", "-C", str(root),
            "cat-file", "--batch",
        ],
        env=git_environment(),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=stderr,
    )


@contextmanager
def open_blob_batch(root):
    with start_blob_batch(root, stderr=subprocess.DEVNULL) as process:
        try:
            yield process
            process.stdin.close()
            if process.wait(timeout=120):
                raise ValueError("Git object read failed")
        except BaseException:
            process.kill()
            process.wait(timeout=30)
            raise


def read_pinned_blob(process, asset):
    oid = asset["git_blob"].encode("ascii")
    expired = Event()

    def interrupt_read():
        expired.set()
        process.kill()

    timer = Timer(120, interrupt_read)
    timer.start()
    try:
        process.stdin.write(oid + b"\n")
        process.stdin.flush()
        header = process.stdout.readline(128)
        match = re.fullmatch(rb"([0-9a-f]{40}) blob ([0-9]+)\n", header)
        if match is None or match[1] != oid:
            raise ValueError("invalid Git blob response")
        size = int(match[2])
        if not 8 <= size <= 256 * 1024 * 1024 or size != asset["size_bytes"]:
            raise ValueError("asset size mismatch or input exceeds 256 MiB")
        content = process.stdout.read(size)
        if len(content) != size or process.stdout.read(1) != b"\n":
            raise ValueError("truncated Git blob")
    finally:
        timer.cancel()
        timer.join()
        if expired.is_set():
            raise subprocess.TimeoutExpired(process.args, 120)
    if hashlib.sha256(content).hexdigest() != asset["sha256"] or content[:16].hex() != asset["prefix_hex"]:
        raise ValueError("asset bytes differ from the pinned digest/prefix")
    return content


def load_json(path):
    if not path.is_file() or path.stat().st_size > 32 * 1024 * 1024:
        raise ValueError("JSON input must be a regular file no larger than 32 MiB")
    return json.loads(path.read_text(encoding="utf-8"))


def read_tree(root, revision):
    if git(root, "rev-parse", "--is-shallow-repository").strip() != b"false":
        raise ValueError("historical lineage requires a complete commit and tree graph")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("revision must be a full lowercase Git commit SHA")
    if (
        git(root, "rev-parse", "--verify", revision + "^{commit}").decode().strip()
        != revision
    ):
        raise ValueError("revision does not identify a commit")
    entries = {}
    for row in git(root, "ls-tree", "-rz", "--full-tree", revision).split(b"\0"):
        if not row:
            continue
        metadata, name = row.split(b"\t", 1)
        mode, kind, oid = metadata.decode().split()
        if kind == "blob" and mode in ("100644", "100755"):
            entries[name.decode("utf-8")] = oid
    return entries


def asset_kind(path):
    suffix = Path(path).suffix.lower()
    if path.startswith("re/") and suffix in (".sldprt", ".sldasm", ".f3d", ".f3z"):
        return "native"
    if path.startswith("re/Fusion/Study/") and path.endswith("/ground_truth.json"):
        return "evidence"
    if path.startswith("re/solidworks/measurements/") and suffix == ".json":
        return "evidence"
    if path == "re/data/Inventories/CorpusCensusPerFile.json":
        return "evidence"
    if path.startswith("re/solidworks/corpus/") and suffix == ".md":
        return "historical_notes"
    return None


def family(path):
    if path.startswith("re/Fusion/Study/"):
        return "fusion-imported-study", "discovery"
    if "/Single Turbo Dual Overhead Cam V8 - KDP - 2024/" in path:
        return "solidworks-v8-project", "holdout"
    if path.startswith("re/Fusion/examples/"):
        return "fusion-external-examples", "holdout"
    return "unclassified-native-lineage", "quarantine"


def reserve_splits(assets):
    natives = [item for item in assets if item["kind"] == "native"]
    splits = {item["lineage"]: item["split"] for item in natives}
    parents = {lineage: lineage for lineage in splits}

    def root(lineage):
        while parents[lineage] != lineage:
            parents[lineage] = parents[parents[lineage]]
            lineage = parents[lineage]
        return lineage

    first_by_hash = {}
    for item in natives:
        first = first_by_hash.setdefault(item["sha256"], item["lineage"])
        parents[root(item["lineage"])] = root(first)
    reserved = {}
    for lineage, split in splits.items():
        if split != "quarantine":
            reserved.setdefault(root(lineage), set()).add(split)
    for item in natives:
        if item["split"] != "quarantine" and len(reserved[root(item["lineage"])]) > 1:
            item["split"] = "quarantine"
            item["split_reason"] = "byte_duplicate_connects_reserved_lineages"


def snapshot(root, revision, specs_path):
    specs = load_json(specs_path)
    if not isinstance(specs, dict) or specs.get("specification_version") != 1:
        raise ValueError("unsupported authoring specification version")
    entries = read_tree(root, revision)
    paths = sorted(path for path in entries if asset_kind(path))
    assets = []
    evidence = []
    with start_blob_batch(root) as process:
        try:
            for path in paths:
                process.stdin.write((entries[path] + "\n").encode())
                process.stdin.flush()
                header = process.stdout.readline().decode().split()
                if (
                    len(header) != 3
                    or header[0] != entries[path]
                    or header[1] != "blob"
                ):
                    raise ValueError("invalid Git blob response")
                size = int(header[2])
                if size > 256 * 1024 * 1024:
                    raise ValueError("individual corpus asset exceeds 256 MiB")
                content = process.stdout.read(size)
                if len(content) != size or process.stdout.read(1) != b"\n":
                    raise ValueError("truncated Git blob")
                item = {
                    "path": path,
                    "git_blob": entries[path],
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "size_bytes": size,
                    "kind": asset_kind(path),
                    "prefix_hex": content[:16].hex(),
                }
                if item["kind"] == "native":
                    item["format"] = Path(path).suffix.lower()[1:]
                    item["lineage"], item["split"] = family(path)
                    item["capture_authorship"] = "unverified"
                if item["kind"] == "evidence":
                    evidence.append((path, content))
                assets.append(item)
        except BaseException:
            process.kill()
            raise
        finally:
            process.stdin.close()
            process.stdin = None
            process.wait(timeout=30)
        if process.returncode != 0:
            raise ValueError("Git object read failed")
    reserve_splits(assets)
    native_paths = {item["path"] for item in assets if item["kind"] == "native"}
    observations = [
        inspect_evidence(path, content, native_paths) for path, content in evidence
    ]
    return {
        "manifest_version": 1,
        "source_revision": revision,
        "scope": "tracked SOLIDWORKS/Fusion native files and recorded research evidence",
        "specifications_sha256": hashlib.sha256(specs_path.read_bytes()).hexdigest(),
        "assets": assets,
        "evidence": observations,
        "summary": {
            "native_by_format": dict(
                sorted(
                    Counter(
                        item["format"] for item in assets if item["kind"] == "native"
                    ).items()
                )
            ),
            "evidence_files": len(observations),
            "qualified_pairs": 0,
            "native_acceptance": "not_established",
        },
    }


def check_manifest(root, manifest, specs_path):
    if not isinstance(manifest, dict) or manifest.get("manifest_version") != 1:
        raise ValueError("unsupported manifest version")
    actual = snapshot(root, manifest["source_revision"], specs_path)
    if manifest != actual:
        raise ValueError(
            "manifest differs from pinned Git objects or authoring specifications"
        )
    return actual["summary"]


def main():
    parser = argparse.ArgumentParser(
        description="Pin research inputs without decoding or launching CAD"
    )
    parser.add_argument("command", choices=("snapshot", "check"))
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--revision")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--specifications",
        type=Path,
        default=Path(__file__).with_name("PairSpecs.json"),
    )
    parser.add_argument("--require-pairs", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "snapshot":
            if not args.revision:
                raise ValueError("snapshot requires --revision")
            if args.manifest.exists():
                raise ValueError(
                    "snapshot destination already exists; select a new path"
                )
            manifest = snapshot(args.root, args.revision, args.specifications)
            text = (
                json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False)
                + "\n"
            )
            output = args.manifest.open("x", encoding="utf-8")
            try:
                with output:
                    output.write(text)
            except BaseException:
                args.manifest.unlink(missing_ok=True)
                raise
            summary = manifest["summary"]
        else:
            manifest = load_json(args.manifest)
            summary = check_manifest(args.root, manifest, args.specifications)
        print(json.dumps(summary, sort_keys=True))
        if args.require_pairs and not summary["qualified_pairs"]:
            print(
                "blocked: independently authored and measured native pairs are missing",
                file=sys.stderr,
            )
            return 2
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        RecursionError,
        subprocess.SubprocessError,
    ) as error:
        print(f"corpus error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
