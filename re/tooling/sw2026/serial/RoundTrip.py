from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.Container.Container import SldprtArchive
from Core import ArchiveError
from Classes import registry
from Streams import load_resolved, load_rooted, store_resolved, store_rooted

PLANS = {
    "Contents/Config-0-ResolvedFeatures": ("resolved", None),
    "Contents/CMgr": ("rooted", 3),
    "Contents/Config-0-ModelHeader": ("rooted", 1),
    "Header2": ("rooted", 1),
    "Contents/Config-0": ("rooted", 4),
}
REQUIRED = (
    "Contents/CMgr",
    "Contents/Config-0",
    "Contents/Config-0-ModelHeader",
    "Contents/Config-0-ResolvedFeatures",
    "Contents/Definition",
    "_MO_VERSION_19000/Biography",
    "_MO_VERSION_19000/History",
)


def hexctx(data, position, size=48):
    lo = max(0, position - 16)
    return data[lo:position].hex(" ") + " | " + data[position:position + size].hex(" ")


def plan(name, plans):
    key = re.sub(r"Config-\d+", "Config-0", name)
    if name not in plans and key not in plans:
        raise ArchiveError(f"no stream plan for {name}")
    return plans.get(name, plans.get(key))


def expand(archive, names):
    out = []
    for name in names:
        if "Config-0" not in name:
            out.append(name)
            continue
        pattern = re.compile("^" + re.escape(name).replace("Config\\-0", r"Config\-\d+") + "$")
        matches = sorted(k for k in archive.streams if pattern.fullmatch(k))
        out.extend(matches if matches else [name])
    return list(dict.fromkeys(out))


def usage_summary(records):
    summary = {direction: {
        "used_schemas": set(),
        "provisional_schemas": set(),
        "missing_schemas": set(),
        "raw_operation_count": 0,
    } for direction in ("load", "store")}
    for record in records:
        usage = record.get("schema_usage", {})
        snapshots = [usage.get(direction) for direction in ("load", "store")]
        snapshots.extend(usage.get("dependencies", []))
        for snapshot in snapshots:
            if snapshot is None:
                continue
            current = summary[snapshot["direction"]]
            for key in ("used_schemas", "provisional_schemas", "missing_schemas"):
                current[key].update(snapshot[key])
            current["raw_operation_count"] += len(snapshot["raw_operations"])
    return {direction: {
        key: sorted(value) if isinstance(value, set) else value
        for key, value in current.items()
    } for direction, current in summary.items()}


def stream_roundtrip(archive, name, reg, plans, linked=False, require_proven=False):
    data = archive.get(name)
    if data is None:
        return {"passed": False, "byte_identity_passed": False, "proven_schemas": False, "schema_usage": {"load": None, "store": None, "dependencies": []}, "error": f"required stream is missing: {name}"}
    rec = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "passed": False}
    load_usage, store_usage, dependencies = None, None, []
    try:
        kind, framing = plan(name, plans)
        options = {}
        with reg.track_usage("load", name, role=kind, sources=archive.streams) as load_usage:
            if kind == "resolved":
                doc, ar = load_resolved(data, reg, 19000)
            elif kind == "custom":
                if linked and name.endswith("-ResolvedFeatures"):
                    from defs.ConfigPart import load_config
                    configuration_name = name.removesuffix("-ResolvedFeatures")
                    configuration_data = archive.require(configuration_name)
                    with reg.track_usage("load", configuration_name, role="linked_map_seed", sources=archive.streams) as dependency:
                        dependency_record = {"usage": dependency, "bytes": len(configuration_data), "sha256": hashlib.sha256(configuration_data).hexdigest(), "tail": None}
                        dependencies.append(dependency_record)
                        configuration, configuration_ar = load_config(configuration_data, reg, 19000, archive=archive, name=configuration_name)
                        dependency_record["tail"] = len(configuration.tail)
                        if configuration.tail:
                            raise ArchiveError("configuration has an unread tail before map handoff")
                        options["seed"] = configuration_ar.map_state()
                        rec["seeded_map_count"] = configuration_ar.count
                doc, ar = framing[0](data, reg, 19000, archive=archive, name=name, **options)
            elif kind == "rooted":
                doc, ar = load_rooted(data, reg, framing, 19000)
            else:
                raise ArchiveError(f"unknown stream framing {kind!r}")
        with reg.track_usage("store", name, role=kind) as store_usage:
            if kind == "resolved":
                again = store_resolved(doc, reg, 19000)
            elif kind == "custom":
                again = framing[1](doc, reg, 19000, **options)
            else:
                again = store_rooted(doc, reg, 19000)
        rec.update(roots=len(doc.roots), tail=len(doc.tail), identical=again == data)
        rec["passed"] = again == data and not doc.tail
        rec["map_base"] = ar.base
        rec["map_count"] = ar.count
        if again != data:
            position = next((i for i, (a, b) in enumerate(zip(again, data)) if a != b), min(len(again), len(data)))
            rec.update(first_diff=position, ctx_src=hexctx(data, position), ctx_out=hexctx(again, position))
        if doc.tail:
            position = len(data) - len(doc.tail)
            rec.update(tail_at=position, tail_ctx=hexctx(data, position))
    except Exception as error:
        rec["error"] = repr(error)
        if hasattr(error, "details"):
            rec["details"] = error.details
        rec["trace"] = traceback.format_exc(limit=6)
    finally:
        rec["schema_usage"] = {
            "load": load_usage.snapshot() if load_usage is not None else None,
            "store": store_usage.snapshot() if store_usage is not None else None,
            "dependencies": [{**item["usage"].snapshot(), **{key: value for key, value in item.items() if key != "usage"}} for item in dependencies],
        }
    rec["byte_identity_passed"] = rec["passed"]
    summary = usage_summary([rec])
    completed = load_usage is not None and load_usage.completed and store_usage is not None and store_usage.completed
    completed = completed and all(item["usage"].completed and item["tail"] == 0 for item in dependencies)
    rec["proven_schemas"] = completed and "error" not in rec and rec.get("tail") == 0 and all(not item["provisional_schemas"] and not item["missing_schemas"] for item in summary.values())
    if require_proven and not rec["proven_schemas"]:
        rec["passed"] = False
        issues = {direction: {key: item[key] for key in ("provisional_schemas", "missing_schemas") if item[key]} for direction, item in summary.items() if item["provisional_schemas"] or item["missing_schemas"]}
        rec.setdefault("error", f"used provisional or missing archive schemas: {issues}" if issues else "archive schema usage is incomplete")
    return rec


def one(path, names, reg, plans, linked=False, require_proven=False):
    report = {"path": str(path), "streams": {}, "passed": False, "byte_identity_passed": False, "proven_schemas": False, "schema_usage": usage_summary([])}
    try:
        raw = Path(path).read_bytes()
        report["sha256"] = hashlib.sha256(raw).hexdigest()
        archive = SldprtArchive.from_bytes(raw, path)
        versions = {name.split("/", 1)[0] for name in archive.streams if name.startswith("_MO_VERSION_")}
        if versions != {"_MO_VERSION_19000"}:
            raise ArchiveError(f"expected SOLIDWORKS 2026 version 19000, found {sorted(versions)}")
        selected = names
        if selected is None:
            selected = list(REQUIRED)
            selected.extend(name for name in plans if name not in REQUIRED and name in archive.streams)
        streams = {name: stream_roundtrip(archive, name, reg, plans, linked, require_proven) for name in expand(archive, selected)}
        report["streams"] = streams
        report["schema_usage"] = usage_summary(streams.values())
        report["byte_identity_passed"] = bool(streams) and all(item.get("byte_identity_passed", False) for item in streams.values())
        report["proven_schemas"] = bool(streams) and all(item.get("proven_schemas", False) for item in streams.values())
        report["passed"] = bool(streams) and all(item["passed"] for item in streams.values())
    except Exception as error:
        report["error"] = repr(error)
        report["trace"] = traceback.format_exc(limit=6)
    return report


def main():
    parser = argparse.ArgumentParser(description="Research-only 2026 stream byte-identity check")
    parser.add_argument("pattern")
    parser.add_argument("streams", nargs="?", help="comma-separated required stream names")
    parser.add_argument("--report", type=Path)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--link-config", action="store_true")
    parser.add_argument("--require-proven", action="store_true", help="reject provisional or missing schemas actually used by selected streams and dependencies")
    args = parser.parse_args()
    names = args.streams.split(",") if args.streams is not None else None
    if names is not None and any(not name for name in names):
        parser.error("stream names must be nonempty")
    paths = sorted({path for path in glob.glob(args.pattern, recursive=True) if Path(path).is_file() and not Path(path).name.startswith("~$")})
    reg = registry()
    plans = {**PLANS, **reg.plans}
    files = [one(path, names, reg, plans, args.link_config, args.require_proven) for path in paths]
    streams = [item for file in files for item in file["streams"].values()]
    usage = usage_summary(streams)
    report = {
        "version": 19000,
        "files": files,
        "file_count": len(files),
        "stream_count": len(streams),
        "passed_streams": sum(item["passed"] for item in streams),
        "passed": bool(files) and all(file["passed"] for file in files),
        "linked_configurations": args.link_config,
        "provisional_schemas": sorted(reg.tentative),
        "schema_usage": usage,
        "used_provisional_schemas": sorted({name for item in usage.values() for name in item["provisional_schemas"]}),
        "require_proven": args.require_proven,
        "byte_identity_passed": bool(files) and all(file["byte_identity_passed"] for file in files),
        "proven_schemas": bool(files) and all(file["proven_schemas"] for file in files),
    }
    if not paths:
        report["error"] = "no input files matched"
    for file in files:
        if "error" in file:
            print("BAD", file["path"], file["error"])
        for name, item in file["streams"].items():
            print("OK " if item["passed"] else "BAD", Path(file["path"]).name, name, {key: value for key, value in item.items() if key not in ("trace", "schema_usage")})
            if args.verbose and "trace" in item:
                print(item["trace"])
    if args.require_proven:
        print(f"{report['passed_streams']}/{len(streams)} streams pass byte identity, tail and proven-schema checks across {len(files)} files")
    else:
        print(f"{report['passed_streams']}/{len(streams)} streams round-trip with no tail across {len(files)} files")
    if "error" in report:
        print(report["error"], file=sys.stderr)
    if args.report is not None:
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
