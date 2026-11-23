import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory

SOLIDWORKS_CHUNK_SIZE = 8


def run_reader(root, script, arguments):
    result = subprocess.run(
        [sys.executable, str(root / "re/automation" / script), *arguments],
        cwd=root, capture_output=True, text=True, timeout=1200, check=False,
    )
    if result.returncode not in (0, 3):
        raise RuntimeError(f"{script}: {result.returncode}: {result.stderr[-4096:]}")
    return result.stdout


def inventory(directory, asset, revision):
    document_bytes = (directory / "document.json").read_bytes()
    document = json.loads(document_bytes)
    receipt = json.loads((directory / "receipt.json").read_bytes())
    if receipt["sdk_revision"] != revision or receipt["source"]["path"] != asset:
        raise ValueError("reader receipt does not identify the requested source and asset")
    if receipt["neutral_sha256"] != hashlib.sha256(document_bytes).hexdigest():
        raise ValueError("reader output differs from its receipt")
    steps = document["feature_timeline"]["$tuple"]
    statuses = {record["path"]: record["status"] for record in receipt["records"]}
    features = []
    for index, step in enumerate(steps):
        definition = step.get("definition")
        features.append({
            "id": step["id"], "name": step.get("name"),
            "kind": step["kind"], "definition_type": definition.get("$type") if definition else None,
            "status": statuses[f"/feature_timeline/$tuple/{index}"],
            "sketch_id": step.get("sketch_id"), "definition": definition,
        })
    return {
        "path": asset, "outcome": "decoded", "reader_mode": receipt.get("reader_mode", "strict"),
        "directory": str(directory), "neutral_sha256": receipt["neutral_sha256"],
        "features": features,
        "definition_types": dict(Counter(feature["definition_type"] or "no_definition" for feature in features)),
        "sketches": len(document["sketches"]["$tuple"]),
        "parameters": len(document["parameters"]["$tuple"]),
        "bodies": len(document["bodies"]["$tuple"]),
        "unresolved": len(receipt["unresolved"]),
        "semantic_qualification": receipt["semantic_qualification"],
        "portable_complete": receipt["portable_complete"],
        "native_acceptance": receipt["native_acceptance"],
    }


def fusion_chunk(root, output, paths, revision):
    arguments = ["--allow-partial", "--output", str(output)]
    for path in paths:
        arguments.extend(("--asset", path))
    run_reader(root, "FusionReader.py", arguments)
    summary = json.loads((output / "summary.json").read_bytes())
    results = []
    for asset in summary["assets"]:
        if asset["outcome"] == "decoded":
            results.append(inventory(output / asset["directory"], asset["path"], revision))
        else:
            results.append(asset)
    return results


def solidworks_chunk(root, output, paths, revision):
    with TemporaryDirectory(prefix=".reader-chunk-", dir=output) as temporary:
        batch = Path(temporary) / "Decoded"
        arguments = ["--batch", "--output", str(batch)]
        for path in paths:
            arguments.extend(("--asset", path))
        run_reader(root, "SolidworksReader.py", arguments)
        summary = json.loads((batch / "summary.json").read_bytes())
        directories = [hashlib.sha256(path.encode()).hexdigest() for path in paths]
        if summary["sdk_revision"] != revision or [
            (entry["path"], entry["directory"]) for entry in summary["assets"]
        ] != list(zip(paths, directories, strict=True)):
            raise ValueError("SOLIDWORKS batch summary differs from the requested roster")
        results = []
        for path, directory in zip(paths, directories, strict=True):
            target = output / directory
            (batch / directory).rename(target)
            results.append(inventory(target, path, revision))
        return results


def solidworks_part(root, output, path, revision):
    target = output / hashlib.sha256(path.encode()).hexdigest()
    run_reader(root, "SolidworksReader.py", ["--asset", path, "--output", str(target)])
    return inventory(target, path, revision)


def main():
    parser = argparse.ArgumentParser(description="Persist actual native CAD feature decodes and their unresolved evidence")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    if not re.fullmatch("[0-9a-f]{40}", args.revision):
        raise ValueError("revision must be a full immutable SHA")
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if actual != args.revision:
        raise ValueError("source checkout differs from requested revision")
    args.output.mkdir(parents=True, exist_ok=False)
    assets = json.loads((root / "re/automation/Corpus.json").read_bytes())["assets"]
    fusion = sorted(asset["path"] for asset in assets if asset.get("format") in ("f3d", "f3z"))
    solidworks = sorted(asset["path"] for asset in assets if asset.get("format") == "sldprt")
    if len(fusion) != 714 or len(solidworks) != 58:
        raise ValueError("the pinned corpus inventory changed; review the session scope")
    with ThreadPoolExecutor(max_workers=4) as workers:
        futures = [workers.submit(fusion_chunk, root, args.output / f"Fusion-{index}", fusion[index::8], actual) for index in range(8)]
        results = [entry for future in futures for entry in future.result()]
        solidworks_output = args.output / "Solidworks"
        solidworks_output.mkdir(mode=0o700)
        reader_help = run_reader(root, "SolidworksReader.py", ["--help"])
        if re.search(r"(?m)^\s+--batch\s", reader_help):
            futures = [
                workers.submit(
                    solidworks_chunk, root, solidworks_output,
                    solidworks[index:index + SOLIDWORKS_CHUNK_SIZE], actual,
                )
                for index in range(0, len(solidworks), SOLIDWORKS_CHUNK_SIZE)
            ]
            results.extend(entry for future in futures for entry in future.result())
        else:
            futures = [
                workers.submit(solidworks_part, root, solidworks_output, path, actual)
                for path in solidworks
            ]
            results.extend(future.result() for future in futures)
    definitions = Counter()
    for result in results:
        definitions.update(result.get("definition_types", {}))
        if "directory" in result:
            result["directory"] = str(Path(result["directory"]).relative_to(args.output))
    summary = {
        "source_revision": actual, "assets": len(results),
        "outcomes": dict(Counter(entry.get("reader_mode", entry["outcome"]) for entry in results)),
        "definition_types": dict(sorted(definitions.items())),
        "feature_steps": sum(len(entry.get("features", [])) for entry in results),
        "sketches": sum(entry.get("sketches", 0) for entry in results),
        "parameters": sum(entry.get("parameters", 0) for entry in results),
        "semantic_qualification": "unverified", "portable_complete": False,
        "native_acceptance": "not_established", "files": sorted(results, key=lambda entry: entry["path"]),
    }
    (args.output / "FeatureInventory.json").write_text(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({key: value for key, value in summary.items() if key != "files"}, sort_keys=True))
    if any(entry["outcome"] == "reader_error" for entry in results):
        raise RuntimeError("the feature session encountered an unexpected reader error")


if __name__ == "__main__":
    main()
