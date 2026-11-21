from argparse import ArgumentParser
from base64 import b64decode
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from subprocess import run
from sys import executable
import json


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def checked(root, row):
    path = (root / row["path"]).resolve(strict=True)
    require(path.is_relative_to(root) and path.is_file(), "box evidence path escapes the packet")
    data = path.read_bytes()
    require(sha256(data).hexdigest() == row["sha256"], "box evidence input changed")
    return data


def worker(kit, request):
    command = [executable, "-I", "-B", str(kit / "re/tooling/sw2026/SdkFreecadBoxProcess.py"), str(kit)]
    return run(command, input=request, capture_output=True, timeout=90, check=False)


def generated(case, kit, request, expected, cache_present):
    result = worker(kit, request)
    require(result.returncode == 0 and not result.stderr, f"{case}: {result.stderr.decode(errors='replace')[-1800:]}")
    value = json.loads(result.stdout)
    require(value == expected and value["runtime_input_file_reads"] == 0, f"{case}: build or owner changed")
    raw = b64decode(value["blob"], validate=True)
    require(len(raw) == value["bytes"] and sha256(raw).hexdigest() == value["sha256"],
            f"{case}: build bytes differ from source label receipt")
    return {
        "case": case, "request_sha256": sha256(request).hexdigest(), "stdout_sha256": sha256(result.stdout).hexdigest(),
        "generated_sha256": value["sha256"], "bytes": value["bytes"], "streams": value["streams"],
        "runtime_input_file_reads": value["runtime_input_file_reads"], "source_cache_present": cache_present,
    }


def negatives(kit, request):
    request = deepcopy(request)
    request["document"]["brep"] = None
    request["document"]["brep_payloads"] = {"$tuple": []}
    other_target = deepcopy(request)
    other_target["native_path"] = other_target["native_path"].rsplit("\\", 1)[0] + "\\Other.SLDPRT"
    selected_length = deepcopy(request)
    drivers = selected_length["document"]["parameters"]["$tuple"]
    length = next(row for row in drivers if row["attributes"]["freecad_path"] == "Length")
    length["value"]["value"] += 1.0
    other_config = deepcopy(request)
    other_config["document"]["configurations"]["$tuple"][0]["attributes"]["unexpected"] = True
    rows = []
    for name, candidate, reason in (
        ("foreign-target", other_target, "native self filename must match"),
        ("disagreeing-driver", selected_length, "three positive independent source dimensions"),
        ("unmapped-configuration", other_config, "actual body, material or configuration ownership"),
    ):
        data = json.dumps(candidate, sort_keys=True, allow_nan=False).encode()
        result = worker(kit, data)
        error = result.stderr.decode(errors="replace")
        require(result.returncode != 0 and not result.stdout and reason in error
                and "construction attempted runtime access" not in error, f"{name}: {error[-1600:]}")
        rows.append({"case": name, "request_sha256": sha256(data).hexdigest(), "rejection": error.splitlines()[-1]})
    return rows


def main():
    parser = ArgumentParser(description="Compare shared SDK origin-box builds with the frozen, native-tested outputs")
    parser.add_argument("kit", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args()
    kit = args.kit.resolve(strict=True)
    manifest_path = args.manifest.resolve(strict=True)
    require(not args.output.exists(), "output proof path must be unused")
    manifest_bytes = manifest_path.read_bytes()
    require(sha256(manifest_bytes).hexdigest() == args.manifest_sha256, "box comparison packet changed")
    manifest = json.loads(manifest_bytes)
    require(manifest["schema"] == "kit.sw2026.freecad-box-shared-inputs.v1"
            and set(manifest["cases"]) == {"initial", "source-labels"}, "box comparison cohort differs")
    rows = []
    for case, files in manifest["cases"].items():
        data = checked(manifest_path.parent, files["request"])
        expected = json.loads(checked(manifest_path.parent, files["expected"]))
        decoded = json.loads(data)
        require(decoded["document"]["source"]["sha256"] == expected["source_sha256"] == manifest["source_sha256"],
                "box comparison source ownership changed")
        for attempt in (1, 2):
            rows.append(generated(f"{case}-{attempt}", kit, data, expected, True))
        decoded["document"]["brep"] = None
        decoded["document"]["brep_payloads"] = {"$tuple": []}
        trimmed = json.dumps(decoded, sort_keys=True, allow_nan=False).encode()
        cache_free_expected = deepcopy(expected)
        cache_free_expected["geometry"]["source_cache_compared"] = False
        rows.append(generated(f"{case}-no-cache", kit, trimmed, cache_free_expected, False))
    rejected = negatives(kit, decoded)
    out = {
        "schema": "kit.sw2026.freecad-box-shared-build.v1", "passed": True,
        "manifest_sha256": args.manifest_sha256, "source_sha256": manifest["source_sha256"],
        "guarded_processes": len(rows) + len(rejected), "builds": rows, "rejections": rejected,
        "heldout_inputs_read": 0, "complete_corpus_conversions": 0, "public_writer_qualified": False,
    }
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
