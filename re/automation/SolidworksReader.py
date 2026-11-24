import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import replace
from pathlib import Path, PurePosixPath

from Corpus import git, open_blob_batch, read_pinned_blob, read_tree
from ReaderEvidence import reader_evidence


def load_manifest(manifest_path):
    with manifest_path.open("rb") as source:
        manifest_bytes = source.read(32 * 1024 * 1024 + 1)
    if len(manifest_bytes) > 32 * 1024 * 1024:
        raise ValueError("manifest exceeds 32 MiB")
    manifest = json.loads(manifest_bytes)
    if not isinstance(manifest, dict) or manifest.get("manifest_version") != 1:
        raise ValueError("unsupported corpus manifest")
    if not isinstance(manifest.get("assets"), list) or len(manifest["assets"]) > 10000 or any(not isinstance(asset, dict) for asset in manifest["assets"]):
        raise ValueError("manifest assets must contain at most 10000 records")
    return manifest, manifest_bytes


def pinned_asset(manifest, entries, asset_path):
    if not 1 <= len(asset_path) <= 4096 or PurePosixPath(asset_path).is_absolute() or ".." in PurePosixPath(asset_path).parts:
        raise ValueError("asset must be a bounded repository-relative path")
    matches = [asset for asset in manifest["assets"] if asset["path"] == asset_path]
    if len(matches) != 1:
        raise ValueError("asset must occur exactly once in the manifest")
    asset = matches[0]
    if asset.get("kind") != "native" or asset.get("format") != "sldprt" or Path(asset_path).suffix.casefold() != ".sldprt":
        raise ValueError("this reader accepts pinned SLDPRT parts only")
    if not re.fullmatch(r"[0-9a-f]{40}", asset["git_blob"]) or entries.get(asset_path) != asset["git_blob"]:
        raise ValueError("asset blob does not match its pinned revision/path")
    return asset


def source_digests(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted((root / "src").rglob("*.py"))}


def write_private(path, payload):
    with path.open("xb") as target:
        os.chmod(target.name, 0o600)
        target.write(payload)
        target.flush()
        os.fsync(target.fileno())


def prepare_reader(root, configuration):
    sys.path.insert(0, str(root / "src"))
    from convert.adapters.solidworks.Core.Adapter import ReadSldprt
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Container.Format import KitDocStream
    from interchange.Core.Common import FreezeMapping
    from interchange.document.Models.DocumentModel import CadDocument

    def read(content, asset_path):
        archive = SldprtArchive.from_bytes(content, asset_path)
        if archive.get(KitDocStream) is not None:
            raise ValueError("embedded Kit documents are not independent native reader evidence")
        document = ReadSldprt(content, Config=configuration)
        document = replace(
            document,
            metadata=FreezeMapping({**document.metadata, "kit.research_read_status": "unqualified"}),
        )
        document.assert_valid()
        encoded = document.to_json(indent=None).encode("utf-8")
        if len(encoded) > 64 * 1024 * 1024:
            raise ValueError("neutral artifact exceeds 64 MiB")
        rebuilt = CadDocument.from_json(encoded.decode("utf-8"))
        rebuilt.assert_valid()
        if rebuilt.to_json(indent=None).encode("utf-8") != encoded:
            raise ValueError("neutral serialization changed after typed reconstruction")
        return archive, encoded

    return read


def write_asset(asset, content, identity, directory, read):
    identity = {**identity, "source": asset}
    fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    archive, encoded = read(content, asset["path"])
    receipt = {
        **identity, "fingerprint": fingerprint,
        "neutral_sha256": hashlib.sha256(encoded).hexdigest(),
        "serialization": "CadDocument JSON", "validation": "model_and_reconstruction_passed",
        "streams": sorted(archive.streams), **reader_evidence(json.loads(encoded)),
    }
    receipt_bytes = (json.dumps(receipt, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    if len(receipt_bytes) > 32 * 1024 * 1024:
        raise ValueError("evidence receipt exceeds 32 MiB")
    write_private(directory / "document.json", encoded)
    write_private(directory / "receipt.json", receipt_bytes)
    return {
        "fingerprint": fingerprint, "neutral_sha256": receipt["neutral_sha256"],
        "counts": receipt["counts"],
    }, len(encoded) + len(receipt_bytes)


def decode(root, manifest_path, asset_path, configuration, output):
    return decode_assets(root, manifest_path, [asset_path], configuration, output, batch=False)


def decode_assets(root, manifest_path, asset_paths, configuration, output, *, batch=True):
    if output.exists() or output.is_symlink():
        raise ValueError("output already exists; select an unused directory")
    if not 1 <= len(asset_paths) <= 1000 or len(set(asset_paths)) != len(asset_paths):
        raise ValueError("select 1–1000 distinct assets")
    manifest, manifest_bytes = load_manifest(manifest_path)
    revision = manifest["source_revision"]
    entries = read_tree(root, revision)
    assets = [pinned_asset(manifest, entries, path) for path in asset_paths]
    source_files = source_digests(root)
    tool_files = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ("SolidworksReader.py", "ReaderEvidence.py", "Corpus.py", "Evidence.py")}
    source_digest = hashlib.sha256(json.dumps(source_files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    options = {"configuration": configuration, "strict": True, "include_brep": True, "include_tessellation": True}
    identity = {
        "corpus_revision": revision, "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "sdk_revision": git(root, "rev-parse", "HEAD").decode().strip(),
        "sdk_sources_sha256": source_digest, "tool_sources": tool_files,
        "python": sys.version, "options": options, "receipt_version": 1,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".reader-", dir=output.parent))
    try:
        results = []
        written = 0
        read = None
        with open_blob_batch(root) as process:
            for asset in assets:
                content = read_pinned_blob(process, asset)
                if read is None:
                    read = prepare_reader(root, configuration)
                directory = staging
                if batch:
                    directory = staging / hashlib.sha256(asset["path"].encode("utf-8")).hexdigest()
                    directory.mkdir(mode=0o700)
                result, size = write_asset(asset, content, identity, directory, read)
                del content
                written += size
                if written > 4 * 1024 * 1024 * 1024:
                    raise ValueError("run output exceeds 4 GiB; select fewer assets")
                if batch:
                    result = {**result, "path": asset["path"], "directory": directory.name}
                results.append(result)
        if source_files != source_digests(root) or identity["sdk_revision"] != git(root, "rev-parse", "HEAD").decode().strip():
            raise ValueError("SDK source changed during decoding; retry against a stable checkout")
        if batch:
            summary = {
                **identity, "assets": results, "counts": {"assets": len(results)},
                "semantic_qualification": "unverified", "portable_complete": False,
                "native_acceptance": "not_established",
            }
            write_private(staging / "summary.json", (json.dumps(summary, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8"))
            if output.exists() or output.is_symlink():
                raise ValueError("output already exists; select an unused directory")
            os.rename(staging, output)
            return {"output": str(output), "assets": results, "counts": summary["counts"], "portable_complete": False}
        output.mkdir(mode=0o700)
        try:
            for name in ("document.json", "receipt.json"):
                os.replace(staging / name, output / name)
        except BaseException:
            shutil.rmtree(output)
            raise
        return {"output": str(output), **results[0], "portable_complete": False}
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main():
    parser = argparse.ArgumentParser(description="Decode pinned SOLIDWORKS parts into research neutral JSON and explicit evidence")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("Corpus.json"))
    parser.add_argument("--asset", required=True, action="append")
    parser.add_argument("--batch", action="store_true", help="decode every supplied asset in order into a batch directory")
    parser.add_argument("--configuration")
    parser.add_argument("--native-verify", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.root.resolve() != Path(__file__).resolve().parents[2]:
            raise ValueError("root must be this reader's SDK checkout")
        if args.configuration is not None and not 1 <= len(args.configuration) <= 256:
            raise ValueError("configuration must contain 1–256 characters")
        if args.batch:
            result = decode_assets(args.root.resolve(), args.manifest, args.asset, args.configuration, args.output)
        else:
            result = decode(args.root.resolve(), args.manifest, args.asset[-1], args.configuration, args.output)
        if args.native_verify:
            from NativeAcceptance.ReaderBatch import VerifyReader

            directories = [args.output / entry["directory"] for entry in result["assets"]] if args.batch else None
            verification = VerifyReader(args.root.resolve(), "solidworks", args.output, directories=directories)
            result["native_verification"] = {key: verification[key] for key in ("status", "action") if key in verification}
        print(json.dumps(result, sort_keys=True))
        if args.native_verify and verification["status"] != "passed":
            return 4 if verification["status"] == "api_unavailable" else 5
        return 0
    except (OSError, ValueError, KeyError, TypeError, RecursionError, subprocess.SubprocessError) as error:
        print(json.dumps({"error": str(error)[:2048], "portable_complete": False}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
