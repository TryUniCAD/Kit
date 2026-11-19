import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
from importlib.metadata import distributions
import json
from pathlib import Path
import subprocess
import sys
import time


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def publish(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )


def verify_code(root):
    manifest = json.loads((root / "CodeManifest01.json").read_bytes())
    for relative, row in manifest["files"].items():
        if digest(root / "CodeRoot" / relative) != row["sha256"]:
            raise ValueError("frozen SDK source changed")


def run(args):
    root = args.root.resolve(strict=True)
    inventory = root / "AvailableNeutralSources.json"
    if (
        digest(inventory)
        != "db7280b68f5bd30d5d3a3f8e3fe92b1ed335e7cd76786ae5cfbddb0064efa52c"
    ):
        raise ValueError("the exact disclosed inventory changed")
    inputs = json.loads(inventory.read_bytes())["inputs"]
    if len(inputs) != 162 or len({row["sha256"] for row in inputs}) != 162:
        raise ValueError("the declared distinct source roster changed")
    verify_code(root)
    original_paths = [value for row in inputs for value in row["paths"]]
    verified = []
    for index, row in enumerate(inputs, 1):
        for alias, value in enumerate(row["paths"], 1):
            source = Path(value)
            if (
                not source.is_file()
                or source.stat().st_size != row["bytes"]
                or digest(source) != row["sha256"]
            ):
                raise ValueError("a disclosed original path or digest changed")
            verified.append(
                {
                    "case_id": f"C{index:03d}-P{alias:02d}",
                    "content_id": f"C{index:03d}",
                    "path_alias": alias,
                    "source_path": value,
                    "sha256": row["sha256"],
                    "bytes": row["bytes"],
                    "object_types": row["object_types"],
                }
            )
    if len(verified) != 171:
        raise ValueError("the physical source count changed")
    publish(
        root / "VerifiedInputs01.json",
        {
            "inventory_sha256": digest(inventory),
            "physical_paths": 171,
            "distinct_sources": 162,
            "files": verified,
        },
    )
    worker = Path(__file__).with_name("CensusFcstdWorker01.py")
    methods = {
        "schema": "kit.sw2026.public-fcstd-census-method.v1",
        "inventory_sha256": digest(inventory),
        "source_manifest_sha256": digest(root / "CodeManifest01.json"),
        "worker_sha256": digest(worker),
        "coordinator_sha256": digest(Path(__file__)),
        "python": sys.version,
        "distributions": sorted(
            (item.metadata["Name"], item.version) for item in distributions()
        ),
        "read_entry": "convert.open_document(original_source_path, strict=True, include_brep=True, include_tessellation=True)",
        "write_entry": "convert.write_document(unchanged_document, owned_path, destination_format=actual_document_kind, allow_carrier=False, overwrite=False, validate=True, values=strict_native_policy)",
        "normal_registry_unchanged": True,
        "original_paths_preserved": True,
        "all_alias_paths_attempted": True,
        "native_processes_started": 0,
        "native_acceptance": False,
        "historical_165_plus_5_membership_verified": False,
        "max_workers": args.workers,
        "timeout_seconds": args.timeout,
    }
    publish(root / "Method01.json", methods)
    requests = []
    for row in verified:
        request = {
            "attempt_root": str(root),
            "guest_attempt_root": args.guest_root,
            "case_id": row["case_id"],
            "source_path": row["source_path"],
            "source_sha256": row["sha256"],
            "object_types": row["object_types"],
            "declared_source_paths": original_paths,
            "method_sha256": digest(root / "Method01.json"),
        }
        path = root / "Requests" / (row["case_id"] + ".json")
        publish(path, request)
        requests.append((row, path))

    def one(item):
        row, path = item
        directory = root / "Cases" / row["case_id"]
        started = time.monotonic()
        try:
            process = subprocess.run(
                [sys.executable, "-B", str(worker), "case", str(path)],
                capture_output=True,
                text=True,
                timeout=args.timeout,
            )
            raw_out = process.stdout
            raw_error = process.stderr
            exit_code = process.returncode
            timed_out = False
        except subprocess.TimeoutExpired as error:
            raw_out = error.stdout or b""
            raw_error = error.stderr or b""
            raw_out = (
                raw_out.decode(errors="replace")
                if isinstance(raw_out, bytes)
                else raw_out
            )
            raw_error = (
                raw_error.decode(errors="replace")
                if isinstance(raw_error, bytes)
                else raw_error
            )
            exit_code = None
            timed_out = True
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "Worker.stdout").write_text(raw_out)
        (directory / "Worker.stderr").write_text(raw_error)
        record = {
            "case_id": row["case_id"],
            "content_id": row["content_id"],
            "input_sha256": row["sha256"],
            "object_types": row["object_types"],
            "request_sha256": digest(path),
            "exit_code": exit_code,
            "timed_out": timed_out,
            "elapsed_seconds": time.monotonic() - started,
            "stdout_sha256": digest(directory / "Worker.stdout"),
            "stderr_sha256": digest(directory / "Worker.stderr"),
        }
        result = directory / "Result.json"
        if result.is_file():
            record.update(
                result_sha256=digest(result), result=json.loads(result.read_bytes())
            )
        if record.get("result", {}).get("public_write_returned"):
            try:
                back = subprocess.run(
                    [
                        sys.executable,
                        "-B",
                        str(worker),
                        "readback",
                        str(directory / "ReadbackRequest.json"),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=args.timeout,
                )
                (directory / "Readback.stdout").write_text(back.stdout)
                (directory / "Readback.stderr").write_text(back.stderr)
                record["readback_exit_code"] = back.returncode
                readback = directory / "Readback.json"
                if readback.is_file():
                    record["readback"] = {
                        "sha256": digest(readback),
                        "result": json.loads(readback.read_bytes()),
                    }
            except subprocess.TimeoutExpired:
                record["readback_timed_out"] = True
        return record

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(one, item): item[0]["case_id"] for item in requests}
        for future in as_completed(futures):
            row = future.result()
            results.append(row)
            if (
                len(results) % 10 == 0
                or row.get("result", {}).get("public_write_returned")
                or len(results) == len(requests)
            ):
                print(
                    json.dumps(
                        {
                            "completed": len(results),
                            "total": len(requests),
                            "strict_reads": sum(
                                v.get("result", {}).get("strict_read_passed", False)
                                for v in results
                            ),
                            "public_writes": sum(
                                v.get("result", {}).get("public_write_returned", False)
                                for v in results
                            ),
                            "timeouts": sum(v["timed_out"] for v in results),
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
    verify_code(root)
    for row in verified:
        if digest(Path(row["source_path"])) != row["sha256"]:
            raise ValueError("an original source changed")
    results.sort(key=lambda row: row["case_id"])
    content_groups = {}
    for row in results:
        content_groups.setdefault(row["content_id"], []).append(row)
    read_success = sum(
        row.get("result", {}).get("strict_read_passed", False) for row in results
    )
    write_success = sum(
        row.get("result", {}).get("public_write_returned", False) for row in results
    )
    diagnostic_counts = {}
    for row in results:
        for key, value in (
            row.get("result", {}).get("pure_admission_diagnostics", {}).items()
        ):
            diagnostic_counts.setdefault(key, Counter())[
                value.get("message", "passed")
            ] += 1
    public_errors = Counter(
        row.get("result", {})
        .get("public_refusal", {})
        .get("message", "no_public_refusal_record")
        for row in results
    )
    read_errors = Counter(
        row.get("result", {}).get("case_error", {}).get("message", "unknown")
        for row in results
        if not row.get("result", {}).get("strict_read_passed")
    )
    families = {}
    for content, group in content_groups.items():
        first = group[0]
        for kind in first["object_types"]:
            families.setdefault(kind, []).append(content)
    summary = {
        "schema": "kit.sw2026.public-fcstd-writer-census.v1",
        "inventory_sha256": digest(inventory),
        "method_sha256": digest(root / "Method01.json"),
        "source_manifest_sha256": digest(root / "CodeManifest01.json"),
        "distinct_sources_attempted": len(content_groups),
        "original_paths_attempted": len(results),
        "strict_path_reads": read_success,
        "public_write_returns": write_success,
        "distinct_sources_with_public_write": sum(
            any(r.get("result", {}).get("public_write_returned") for r in group)
            for group in content_groups.values()
        ),
        "writer_output_count": sum(
            row.get("result", {}).get("writer_output_count", 0) for row in results
        ),
        "independent_readback_attempts": sum(
            "readback_exit_code" in row or row.get("readback_timed_out", False)
            for row in results
        ),
        "independent_strict_readbacks": sum(
            row.get("readback", {})
            .get("result", {})
            .get("normal_strict_readback_passed", False)
            for row in results
        ),
        "timeouts": sum(row["timed_out"] for row in results),
        "worker_failures_without_result": sum("result" not in row for row in results),
        "all_original_source_hashes_unchanged": True,
        "all_snapshot_hashes_unchanged": True,
        "public_refusal_counts": dict(public_errors),
        "strict_read_failure_counts": dict(read_errors),
        "unchanged_model_diagnostic_counts": {
            k: dict(v) for k, v in diagnostic_counts.items()
        },
        "family_content_membership_counts": {k: len(v) for k, v in families.items()},
        "native_processes_started": 0,
        "native_acceptance": False,
        "historical_165_plus_5_membership_verified": False,
        "accepted_conversions": 0,
        "results": results,
    }
    publish(root / "Result.json", summary)
    print(
        json.dumps(
            {
                key: value
                for key, value in summary.items()
                if key
                not in {
                    "results",
                    "family_content_membership_counts",
                    "unchanged_model_diagnostic_counts",
                    "public_refusal_counts",
                    "strict_read_failure_counts",
                }
            },
            sort_keys=True,
        ),
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--guest-root", required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=120)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
