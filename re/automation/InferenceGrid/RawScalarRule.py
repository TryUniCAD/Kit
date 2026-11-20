# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter
import difflib
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KSerializedStringMarker
from InferenceGrid.SolidWorksDimensionEvidence import (
    capture_sets,
    dimensions,
    encoding_hits,
    name_records,
)
from InferenceGrid.SolidWorksFieldDiscovery import discovery_inventory
from InferenceInputs import read_file


def trials(root, excluded, target_pin):
    sets = capture_sets(root)
    eligible = discovery_inventory(root, sets)
    specs = json.loads(read_file(root / "re/automation/PairSpecs.json", 1024 * 1024))
    splits = {recipe["id"]: recipe for recipe in specs["recipes"]}
    samples = []
    blobs = {}
    target_observations = []
    for folder, receipt, report, files in sets:
        recipe = splits[receipt["recipe_id"]]
        for edit in report["observations"]["edits"]:
            filename = edit["saved_file"]
            row = files.get(filename)
            if (
                not row
                or Path(filename).name != filename
                or recipe["split"] not in {"discovery", "qualification", "holdout"}
            ):
                continue
            if recipe["split"] == "discovery" and row["sha256"] not in eligible:
                continue
            opened = report["observations"].get("reopened_files", {}).get(filename, {})
            if opened.get("open_status") != {"errors": 0, "warnings": 0}:
                continue
            values = [
                v for _, name, v in dimensions(opened) if name == edit["parameter"]
            ]
            if len(values) != 1 or not values[0]:
                continue
            raw = read_file(folder / filename, 16 * 1024 * 1024)
            if hashlib.sha256(raw).hexdigest() != row["sha256"]:
                continue
            streams = SldprtArchive.FromBytes(raw).Streams
            config_hashes = {
                n: hashlib.sha256(b).hexdigest()
                for n, b in streams.items()
                if n.startswith("Contents/Config-")
            }
            target_members = [
                n for n, digest in config_hashes.items() if digest == target_pin
            ]
            if target_members:
                target_observations.append(
                    {
                        "archive_sha256": row["sha256"],
                        "measurement_sha256": receipt["measurement_receipt_sha256"],
                        "members": target_members,
                        "values": dimensions(opened),
                    }
                )
            windows = []
            for name, end in name_records(streams, edit["parameter"]):
                stream = streams[name]
                digest = hashlib.sha256(stream).hexdigest()
                blobs.setdefault(digest, stream)
                windows.append((digest, end, stream[end : end + 104]))
            if not (
                recipe["split"] == "discovery"
                and (
                    row["sha256"] in excluded
                    or not excluded.isdisjoint(config_hashes.values())
                )
            ):
                samples.append(
                    (
                        {
                            "parameter": edit["parameter"],
                            "value": values[0],
                            "family": recipe["family"],
                            "recipe": recipe["id"],
                            "split": recipe["split"],
                            "archive_sha256": row["sha256"],
                            "measurement_sha256": receipt["measurement_receipt_sha256"],
                        },
                        windows,
                    )
                )
    return samples, blobs, target_observations


def generated_source(fmt, offset, fixed):
    return f"""import argparse
import json
import math
from pathlib import Path
import struct

from InferenceInputs import read_file


def read(data):
    marker = bytes.fromhex("{KSerializedStringMarker.hex()}")
    fixed = {fixed!r}
    matches = []
    cursor = 0
    while (start := data.find(marker, cursor)) >= 0:
        cursor = start + len(marker)
        if cursor >= len(data):
            break
        length = data[cursor]
        end = cursor + 1 + length * 2
        offset = end + {offset}
        if not 0 < length < 255 or offset + {struct.calcsize(fmt)} > len(data):
            continue
        if any(data[end+i] != byte for i, byte in fixed):
            continue
        try:
            label = data[cursor+1:end].decode("utf-16le")
        except UnicodeDecodeError:
            continue
        value = struct.unpack_from({fmt!r}, data, offset)[0]
        if label.isprintable() and math.isfinite(value):
            matches.append({{"name":label, "offset":offset, "value":value}})
            if len(matches) > 16384:
                raise ValueError("too many named scalar records")
    return matches


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--member")
    parser.add_argument("--owners", action="store_true")
    args = parser.parse_args()
    data = read_file(args.source, 128*1024*1024)
    if args.member is not None:
        from convert.adapters.solidworks.Container.Container import SldprtArchive
        archive = SldprtArchive.FromBytes(data)
        data = archive.Require(args.member)
    result = read(data)
    if args.owners:
        if not args.member:
            parser.error("--owners requires --member")
        from InferenceGrid.RawScalarOwners import associate
        result = {{"records":result, "ownership":associate(archive,args.member,result)}}
    print(json.dumps(result, allow_nan=False))
"""


def raw_scalars(root, data, pin, scratch, controls, exclude_archives=()):
    if KSerializedStringMarker not in data:
        return None, None
    excluded = {
        pin,
        *exclude_archives,
        *(hashlib.sha256(blob).hexdigest() for blob in controls),
    }
    samples, blobs, target_observations = trials(root, excluded, pin)
    training = [
        (row, windows) for row, windows in samples if row["split"] == "discovery"
    ]
    if (
        len({row["value"] for row, _ in training}) < 2
        or len({row["parameter"] for row, _ in training}) < 2
    ):
        return None, None
    candidates = None
    for row, windows in training:
        hits = set().union(
            *(encoding_hits(window, 0, row["value"]) for _, _, window in windows)
        )
        candidates = hits if candidates is None else candidates & hits
    if len(candidates or ()) != 1:
        return {
            "status": "ambiguous_encoding",
            "candidates": sorted(candidates or ()),
        }, None
    fmt, offset = candidates.pop()
    headers = [
        window[:offset]
        for row, windows in training
        for _, _, window in windows
        if window[offset : offset + struct.calcsize(fmt)]
        == struct.pack(fmt, row["value"])
    ]
    fixed = tuple(
        (i, values[0])
        for i, values in enumerate(zip(*headers))
        if len(set(values)) == 1
    )
    if len(fixed) < 8:
        return {
            "status": "insufficient_record_context",
            "fixed_positions": len(fixed),
        }, None
    checks = []
    for row, windows in samples:
        readings = [
            (digest, end + offset, struct.unpack_from(fmt, window, offset)[0])
            for digest, end, window in windows
            if len(window) >= offset + struct.calcsize(fmt)
            and all(window[i] == b for i, b in fixed)
        ]
        checks.append(
            {
                **row,
                "matches": bool(readings)
                and all(
                    math.isclose(v, row["value"], rel_tol=1e-12, abs_tol=1e-14)
                    for _, _, v in readings
                ),
                "locations": [[h, pos] for h, pos, _ in readings],
            }
        )
    code = generated_source(fmt, offset, fixed)
    path = scratch / "NamedScalarReader.py"
    path.write_text(code, encoding="utf-8")

    def replay(blob):
        source = scratch / "scalar-input.bin"
        source.write_bytes(blob)
        env = {
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(root / "re/automation"),
        }
        result = subprocess.run(
            [sys.executable, str(path), str(source)],
            cwd=scratch,
            env=env,
            capture_output=True,
            timeout=60,
        )
        if result.returncode:
            raise ValueError("raw scalar reader replay failed")
        return json.loads(result.stdout)

    try:
        records = replay(data)
    except (subprocess.TimeoutExpired, ValueError):
        return {"status": "candidate_reader_refused_input"}, None
    if not records:
        return None, None
    comparisons = []
    for blob in controls:
        try:
            comparison = {"records": replay(blob)}
        except (subprocess.TimeoutExpired, ValueError):
            comparison = {"status": "candidate_reader_refused_control"}
        comparisons.append({"sha256": hashlib.sha256(blob).hexdigest(), **comparison})
    report = {
        "status": "candidate_named_scalars",
        "encoding": fmt,
        "displacement": offset,
        "fixed_header_positions": fixed,
        "trials": checks,
        "records": records,
        "control_replays": comparisons,
    }
    decoded = {pin: records}
    training_streams = {digest for row, windows in training for digest, _, _ in windows}
    for check, (_, windows) in zip(checks, samples):
        offsets = set()
        actual = []
        stream_hashes = {digest for digest, _, _ in windows}
        for digest in stream_hashes:
            if digest not in decoded:
                decoded[digest] = replay(blobs[digest])
            for item in decoded[digest]:
                if item["name"] == check["parameter"]:
                    actual.append(item["value"])
                    offsets.add((digest, item["offset"]))
        check["generated_reader_matches"] = (
            bool(actual)
            and all(
                math.isclose(v, check["value"], rel_tol=1e-12, abs_tol=1e-14)
                for v in actual
            )
            and offsets == set(map(tuple, check["locations"]))
        )
        if check["split"] != "discovery" and stream_hashes & training_streams:
            check["generated_reader_matches"] = False
    confirmed = []
    counts = Counter(r["name"] for r in records)
    for record in records:
        if not target_observations or counts[record["name"]] != 1:
            continue
        corroborated = True
        for obs in target_observations:
            values = [v for _, name, v in obs["values"] if name == record["name"]]
            if len(values) != 1 or not math.isclose(
                values[0], record["value"], rel_tol=1e-12, abs_tol=1e-14
            ):
                corroborated = False
                break
        if corroborated:
            confirmed.append(record["offset"])
    report["target_witnesses"] = [
        {k: v for k, v in obs.items() if k != "values"} for obs in target_observations
    ]
    report["native_measurement_offsets"] = confirmed
    evaluated = {r["split"] for r in checks if r["matches"]}
    if (
        "holdout" not in evaluated
        or "qualification" not in evaluated
        or not all(r["matches"] and r["generated_reader_matches"] for r in checks)
    ):
        return report, None
    relative = "re/solidworks/DerivedReaders/NamedScalarReader.py"
    if (root / relative).exists():
        return report, None
    return report, {
        "patch": "".join(
            difflib.unified_diff(
                [], code.splitlines(True), "/dev/null", "b/" + relative
            )
        ),
        "path": relative,
        "reader_sha256": hashlib.sha256(code.encode()).hexdigest(),
        "input_sha256": pin,
        "base": subprocess.check_output(
            ["git", "-C", root, "rev-parse", "HEAD"], text=True
        ).strip(),
    }


def measured_controls(root, pin, scratch):
    for folder, receipt, report, files in capture_sets(root):
        reopened = report["observations"].get("reopened_files", {})
        readings = {}
        for name in files:
            observation = reopened.get(name, {})
            if observation.get("open_status") != {"errors": 0, "warnings": 0}:
                continue
            values = dimensions(observation)
            fields = {(feature, parameter): value for feature, parameter, value in values}
            if fields and len(fields) == len(values):
                readings[name] = fields
        matches = [name for name in readings if files[name]["sha256"] == pin]
        if len(matches) != 1:
            continue
        before = readings[matches[0]]
        controls = {}
        budget = 64 * 1024 * 1024
        for name, after in sorted(readings.items()):
            if Path(name).name != name or before.keys() != after.keys():
                continue
            changed = [key for key in before if before[key] != after[key]]
            if len(changed) != 1:
                continue
            path = folder / name
            if not path.is_file() or path.stat().st_size > min(budget, 16 * 1024 * 1024):
                continue
            raw = read_file(path, min(budget, 16 * 1024 * 1024))
            digest = hashlib.sha256(raw).hexdigest()
            if digest != files[name]["sha256"] or digest in controls:
                continue
            key = changed[0]
            snapshot = scratch / (digest + ".sldprt")
            snapshot.write_bytes(raw)
            controls[digest] = (snapshot, {
                "feature": key[0], "parameter": key[1], "input_value": before[key],
                "control_value": after[key], "measurement_sha256": receipt["measurement_receipt_sha256"],
            })
            budget -= len(raw)
            if len(controls) == 32:
                break
        return controls
    return {}


def part_scalars(root, source, pin, scratch, controls):
    import re

    archive = SldprtArchive.FromBytes(read_file(source, 128 * 1024 * 1024))
    sections = sorted(
        (r.name, r.data)
        for r in archive.records
        if re.fullmatch(r"Contents/Config-[0-9]+(?:-ResolvedFeatures)?", r.name)
    )
    selected = []
    budget = 32 * 1024 * 1024
    deferred = []
    for name, blob in sorted(
        sections, key=lambda e: (not e[0].endswith("-ResolvedFeatures"), e[0])
    ):
        if KSerializedStringMarker not in blob:
            continue
        if len(selected) >= 8 or len(blob) > budget:
            deferred.append(name)
            continue
        selected.append((name, blob))
        budget -= len(blob)
    result = {"input_sha256": pin, "members": {}, "deferred_members": deferred}
    if not selected:
        return result, None
    private = scratch / "part-scalars"
    private.mkdir()
    pairs = {path.stem: (path, None) for path in controls} if controls else measured_controls(root, pin, private)
    excluded = {pin, *pairs}
    for path, _ in pairs.values():
        control_archive = SldprtArchive.FromBytes(read_file(path, 16 * 1024 * 1024))
        excluded.update(
            hashlib.sha256(record.data).hexdigest()
            for record in control_archive.records
            if record.name.startswith("Contents/Config-")
        )
    for i, (name, blob) in enumerate(selected):
        others = [(k, b) for j, (k, b) in enumerate(selected) if i != j]
        rule, patch = raw_scalars(
            root,
            blob,
            hashlib.sha256(blob).hexdigest(),
            private,
            [b for _, b in others],
            excluded,
        )
        if not rule or "records" not in rule:
            result["members"][name] = {
                "status": rule["status"] if rule else "no_matching_records"
            }
            continue
        result["experiment"] = {
            k: v for k, v in rule.items() if k not in {"records", "control_replays"}
        }
        result["fitting_target"] = name
        result["members"][name] = {
            "records": rule["records"],
            "sha256": hashlib.sha256(blob).hexdigest(),
        }
        for (other, _), replay in zip(others, rule["control_replays"]):
            result["members"][other] = replay
        from InferenceGrid.RawScalarOwners import associate, changed_owner, native_comparisons

        for member, row in result["members"].items():
            if "records" in row:
                row["ownership"] = associate(archive, member, row["records"])
        result["owner_observations"] = native_comparisons(root, pin, result["members"])
        if patch and any("records" not in row for row in result["members"].values()):
            return result, None
        if patch:
            def run_reader(path, member):
                return subprocess.run(
                    [
                        sys.executable,
                        str(private / "NamedScalarReader.py"),
                        str(path),
                        "--member",
                        member,
                        "--owners",
                    ],
                    cwd=private,
                    env={
                        **os.environ,
                        "PYTHONDONTWRITEBYTECODE": "1",
                        "PYTHONPATH": os.pathsep.join(
                            map(str, (root / "src", root / "re/automation"))
                        ),
                    },
                    capture_output=True,
                    timeout=60,
                )
            for member, row in result["members"].items():
                process = run_reader(source, member)
                if process.returncode or json.loads(process.stdout) != {
                    "records": row["records"],
                    "ownership": row["ownership"],
                }:
                    result["status"] = "native_entry_replay_failed"
                    return result, None
            for digest, (path, measured) in pairs.items():
                for member, row in result["members"].items():
                    if not row.get("ownership", {}).get("records"):
                        continue
                    proc = run_reader(path, member)
                    comparison = changed_owner(row, json.loads(proc.stdout)) if not proc.returncode else {"status": "control_reader_refused"}
                    if measured:
                        comparison["native_edit"] = measured
                        comparison["matches_measured_change"] = comparison.get("parameter") == measured["parameter"] and all(
                            math.isclose(comparison[key], measured[key], rel_tol=1e-12, abs_tol=1e-14)
                            for key in ("input_value", "control_value")
                        )
                    row.setdefault("paired_changes", []).append({"control_sha256": digest, **comparison})
            patch = {
                **patch,
                "input_sha256": pin,
                "verified_members": list(result["members"]),
            }
        return result, patch
    return result, None
