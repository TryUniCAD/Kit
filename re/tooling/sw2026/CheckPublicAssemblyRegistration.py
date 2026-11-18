from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")
    return digest(path)


def checked_sources(source, manifest):
    return all(digest(source / name) == expected for name, expected in manifest.items())


def worker(job):
    name, code, script, arguments, output = job
    result = subprocess.run([sys.executable, "-I", "-B", str(code / "re/tooling/sw2026" / script), str(code), *arguments],
                            cwd=code, capture_output=True, text=True, timeout=90)
    (output / (name + ".stdout")).write_text(result.stdout, encoding="utf-8")
    (output / (name + ".stderr")).write_text(result.stderr, encoding="utf-8")
    if result.returncode or result.stderr:
        raise ValueError(f"the isolated public registry process failed: {name}: {result.stderr}")
    observed = json.loads(result.stdout)
    if not observed["passed"] or observed["runtime_input_file_reads"] or observed["native_processes_started"]:
        raise ValueError("the public process lost its actual boundary or runtime-independence checks")
    return name, observed


def run(args):
    code, baseline = (value.resolve(strict=True) for value in (args.code, args.baseline))
    manifest = json.loads(args.source_manifest.read_bytes())
    if not checked_sources(code, manifest["full_sdk_files"]):
        raise ValueError("the frozen public registration SDK source changed")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    modes = [("fresh", 2), ("fresh", 3), ("explicit", 2), ("explicit", 3)]
    modes += [(name, 3) for name in ("child-collision", "case-collision", "directory-collision", "dangling-child", "root-collision",
                                   "overwrite-rejected", "overwrite-empty", "stream-rejected", "missing-mapping", "wrong-mapping", "relative-mapping",
                                   "wrong-format", "unqualified-option", "unsupported-mate", "unqualified-child", "commit-failure", "race-protection")]
    jobs = [(f"{mode}-{count}", code, "PublicAssemblyRegistryProcess.py", [mode, str(count), str(output / f"{mode}-{count}")], output)
            for mode, count in modes]
    jobs += [("native-" + mode, code, "PublicAssemblyRegistryProcess.py",
              [mode, "3", str(output / ("native-" + mode)), str(args.native_request.resolve(strict=True))], output) for mode in ("fresh", "explicit")]
    for role in ("polygon", "diameter-front", "radius-top-reverse"):
        for name, source in (("baseline", baseline), ("integrated", code)):
            jobs.append((name + "-" + role, source, "PublicPartWriteParityProcess.py", [role], output))
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = dict(pool.map(worker, jobs))
    births = [row["worker_pid"] for row in rows.values()]
    if len(births) != len(set(births)) or not checked_sources(code, manifest["full_sdk_files"]):
        raise ValueError("the isolated source closure or process identities changed")
    comparisons = []
    for role in ("polygon", "diameter-front", "radius-top-reverse"):
        first, second = (rows[name + "-" + role] for name in ("baseline", "integrated"))
        if any(first[key] != second[key] for key in ("bytes", "sha256", "document_json", "native_capabilities")):
            raise ValueError("normal assembly registration changed standalone part writing or reading")
        comparisons.append({"profile": role, "bytes": first["bytes"], "sha256": first["sha256"],
                            "strict_document_json_sha256": sha256(first["document_json"].encode()).hexdigest(), "exact": True})
    reader_values = [row["reader"] for row in rows.values() if "reader" in row]
    if not all(row == reader_values[0] for row in reader_values):
        raise ValueError("normal registry read metadata is inconsistent")
    report = {"schema": "kit.sw2026.default-assembly-registration-process-proof.v1", "passed": True,
              "source_manifest_sha256": digest(args.source_manifest), "worker_count": len(rows), "distinct_processes": len(set(births)),
              "sdk_files": len(manifest["full_sdk_files"]), "runtime_input_file_reads": 0, "native_processes_started": 0,
              "registration_changes_are_private_overlay": True, "new_native_acceptance_batch": False,
              "native_output_equivalence": all(rows["native-" + role]["whole_bundle_matches_native_input"] for role in ("fresh", "explicit")),
              "part_preservation": comparisons, "reader_metadata": reader_values[0],
              "concurrent_companion_preserved": rows["race-protection-3"]["concurrent_companion_preserved"],
              "overwrite_closed": True, "direct_windows_path_host_execution": False,
              "processes": {name: {key: value for key, value in row.items() if key != "document_json"} for name, row in rows.items()},
              "process_stdout_sha256": {name: digest(output / (name + ".stdout")) for name in rows}}
    result_sha = write(output / "Result.json", report)
    return {"passed": True, "worker_count": len(rows), "result_sha256": result_sha,
            "concurrent_companion_preserved": report["concurrent_companion_preserved"], "native_processes_started": 0}


def main():
    parser = argparse.ArgumentParser(description="Verify actual default assembly registry dispatch, handled transactions and exact standalone preservation in separate processes")
    parser.add_argument("--code", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--native-request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(run(parser.parse_args()), sort_keys=True))


if __name__ == "__main__":
    main()
