from argparse import ArgumentParser
import json
from pathlib import Path, PureWindowsPath
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))
from CheckMeasuredPattern import (
    PACKET_SHA, ROOT, SOURCE_HASHES, digest, read_inputs, require, stream_manifest, tree_digest,
)


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def checked_member(root, name, expected):
    path = root / name
    require(path.resolve(strict=True).is_relative_to(root) and not path.is_symlink(),
            f"member escaped its evidence root: {name}")
    raw = path.read_bytes()
    require(digest(raw) == expected, f"member digest differs: {name}")
    return raw


def original_packet(original):
    packet = json.loads(checked_member(original, "Packet.json", PACKET_SHA))
    files = packet["files"]
    build = json.loads(checked_member(original, "Build.json", files["Build.json"]))
    require(build["heldout_cases"] == build["native_lifecycles"] == 0
            and set(build["model_cases"]) == set(SOURCE_HASHES),
            "phase predictions must come from the disclosed model build")
    assets = {}
    skip = {"Build.json", *(name + ".SLDPRT" for name in SOURCE_HASHES)}
    for name, expected in files.items():
        if name in skip:
            continue
        if name != "Control.SLDPRT":
            parts = Path(name).parts
            require(len(parts) == 2 and
                    ((parts[0] == "Tools" and Path(name).suffix == ".py")
                     or (parts[0] == "Metadata" and Path(name).suffix == ".json")),
                    "unexpected licensed or unbound packet member")
        assets[name] = checked_member(original, name, expected)
    return packet, build, assets


def capture(root, name, expected_streams, request_sha, sdk_sha):
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    folder = root / name
    report_raw = (folder / "Capture.json").read_bytes()
    report = json.loads(report_raw)
    require(report["capture_schema"] == "kit.sw2026.pattern-compression-capture.v1"
            and report["case"] == name and report["request_sha256"] == request_sha
            and report["sdk_source_sha256"] == sdk_sha
            and report["worker_sha256"] == digest((HERE.parent / "CheckMeasuredPattern.py").read_bytes())
            and report["runtime_input_file_reads"] == report["native_launches"] == 0
            and report["design_only_history_equal"] is True
            and report["strict_history_refusal_count"] == 2
            and report["permissive_history_unqualified"] is True,
            "capture differs from the exact guarded source or request")
    raw = checked_member(folder.resolve(strict=True), name + ".SLDPRT", report["generated_sha256"])
    archive = SldprtArchive.from_bytes(raw)
    require(len(raw) == report["bytes"] and archive.format_version == 4
            and stream_manifest(archive) == report["streams"] == expected_streams,
            "captured archive differs from its native-tested logical streams")
    compressed = {
        row.name: [row.compressed_size, digest(raw[row.payload_offset:row.payload_offset + row.compressed_size])]
        for row in archive.records
    }
    return raw, report, digest(report_raw), archive.file_id, compressed


def native_plan(source, target, identity):
    original = source["original"]
    model = original["modeled_input"]
    locator = model["seed"]["path"]
    require(locator == target["PathName"]
            and model["seed"]["epoch"] == target["SavedAt"]
            and original["native_container"]["sha256"] == SOURCE_HASHES[PureWindowsPath(locator).stem],
            "native expected plan no longer owns the exact writer locator and clock")
    edited = source["pitch_only"]
    return {
        "original": {
            "modeled_input": model,
            "independent_cell_measure": original["independent_cell_measure"],
            "native_container": identity,
        },
        "pitch_only": {key: edited[key] for key in ("modeled_input", "independent_cell_measure")},
    }


def expect_alternate(classic, first, repeat, name):
    base_raw, base, _, base_id, base_rows = classic
    raw, observed, _, file_id, rows = first
    repeated, retry, _, retry_id, retry_rows = repeat
    require(digest(base_raw) == SOURCE_HASHES[name] and base["status"] == "native_hash_reproduced"
            and base["publication_count"] == 7 and "zlib-ng" not in base["compression_runtime"],
            "classic capture did not reproduce the exact native-tested file")
    require(raw == repeated and raw != base_raw
            and file_id == retry_id == base_id and list(rows) == list(retry_rows) == list(base_rows)
            and retry_rows == rows and rows != base_rows
            and observed["semantics"] == retry["semantics"] == base["semantics"],
            "the changed envelope is not an exact independent same-model regeneration")
    require(observed["worker_pid"] != retry["worker_pid"], "repeat must come from a fresh worker")
    for report in (observed, retry):
        require(report["runtime_platform"] == "win32" and "zlib-ng" in report["compression_runtime"]
                and report["status"] == "unmeasured_binary_envelope_refused"
                and report["publication_count"] == 0 and report["refusal_count"] == 2,
                "only independent Windows zlib-ng worker refusals are eligible for this trial")
    require((observed["python_version"], observed["compression_runtime"])
            == (retry["python_version"], retry["compression_runtime"]),
            "alternate captures did not use the same codec runtime")


def stage(original, classic, alternate, repeat, output):
    sys.path.insert(0, str(ROOT / "src"))
    sdk_sha = tree_digest(ROOT / "src")
    previous, original_build, assets = original_packet(original)
    comparison = {
        "schema": "kit.sw2026.pattern-compression-comparison.v1",
        "original_packet_sha256": PACKET_SHA,
        "sdk_source_sha256": sdk_sha,
        "heldout_inputs_read": 0,
        "native_lifecycles": 0,
        "cases": {},
    }
    builds = {}
    for name in SOURCE_HASHES:
        request, _, _, request_sha, expected = read_inputs(ROOT, name)
        captures = [capture(folder, name, expected, request_sha, sdk_sha)
                    for folder in (classic, alternate, repeat)]
        expect_alternate(*captures, name)
        prior, first, _ = captures
        payload = first[0]
        identity = {"sha256": digest(payload), "bytes": len(payload), "version": 4}
        builds[name] = native_plan(original_build["model_cases"][name], request["target"], identity)
        assets[name + ".SLDPRT"] = payload
        comparison["cases"][name] = {
            "classic_sha256": digest(prior[0]),
            "alternate_sha256": digest(payload),
            "alternate_bytes": len(payload),
            "capture_sha256": [value[2] for value in captures],
            "codec_version": first[1]["compression_runtime"],
            "python_version": first[1]["python_version"],
            "logical_streams": expected,
            "changed_compression": [
                name for name, row in first[4].items() if row != prior[4][name]
            ],
        }
    assets["Build.json"] = encode({
        "schema": original_build["schema"],
        "model_cases": builds,
        "heldout_cases": 0,
        "native_lifecycles": 0,
    })
    assets["Compression.json"] = encode(comparison)
    packet = {
        **previous,
        "files": {name: digest(raw) for name, raw in assets.items()},
    }
    packet_data = encode(packet)
    output.mkdir(exist_ok=False)
    for name, raw in sorted({**assets, "Packet.json": packet_data}.items()):
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)
    return {
        "packet_sha256": digest(packet_data),
        "comparison_sha256": digest(assets["Compression.json"]),
        "observer_sha256": packet["files"]["Tools/ObserveGeneratedLinearPattern.py"],
        "cases": len(builds),
        "native_lifecycles": 0,
    }


def main():
    parser = ArgumentParser(description="Stage two independently captured pattern compression variants")
    parser.add_argument("original", type=Path)
    parser.add_argument("--verify-original", action="store_true")
    parser.add_argument("--classic", type=Path)
    parser.add_argument("--alternate", type=Path)
    parser.add_argument("--repeat", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.verify_original:
        _, build, members = original_packet(args.original.resolve())
        case_rows = {}
        for name in SOURCE_HASHES:
            request, _, _, _, _ = read_inputs(ROOT, name)
            source = build["model_cases"][name]
            model = native_plan(source, request["target"], source["original"]["native_container"])
            case_rows[name] = model["original"]["modeled_input"]["seed"]["path"]
        result = {"verified_packet_sha256": PACKET_SHA, "members": len(members), "locators": case_rows}
    else:
        require(all((args.classic, args.alternate, args.repeat, args.output)),
                "stage requires four explicit output or capture paths")
        result = stage(args.original.resolve(), args.classic, args.alternate, args.repeat, args.output)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
