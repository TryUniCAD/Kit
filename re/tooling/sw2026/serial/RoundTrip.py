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

from convert.adapters.solidworks.container.Container import SldprtArchive
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


def stream_roundtrip(archive, name, reg, plans):
    data = archive.get(name)
    if data is None:
        return {"passed": False, "error": f"required stream is missing: {name}"}
    rec = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "passed": False}
    try:
        kind, framing = plan(name, plans)
        if kind == "resolved":
            doc, ar = load_resolved(data, reg, 19000)
            again = store_resolved(doc, reg, 19000)
        elif kind == "custom":
            doc, ar = framing[0](data, reg, 19000, archive=archive, name=name)
            again = framing[1](doc, reg, 19000)
        elif kind == "rooted":
            doc, ar = load_rooted(data, reg, framing, 19000)
            again = store_rooted(doc, reg, 19000)
        else:
            raise ArchiveError(f"unknown stream framing {kind!r}")
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
    return rec


def one(path, names, reg, plans):
    report = {"path": str(path), "streams": {}, "passed": False}
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
        streams = {name: stream_roundtrip(archive, name, reg, plans) for name in expand(archive, selected)}
        report["streams"] = streams
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
    args = parser.parse_args()
    names = args.streams.split(",") if args.streams is not None else None
    if names is not None and any(not name for name in names):
        parser.error("stream names must be nonempty")
    paths = sorted({path for path in glob.glob(args.pattern, recursive=True) if Path(path).is_file() and not Path(path).name.startswith("~$")})
    reg = registry()
    plans = {**PLANS, **reg.plans}
    files = [one(path, names, reg, plans) for path in paths]
    streams = [item for file in files for item in file["streams"].values()]
    report = {
        "version": 19000,
        "files": files,
        "file_count": len(files),
        "stream_count": len(streams),
        "passed_streams": sum(item["passed"] for item in streams),
        "passed": bool(files) and all(file["passed"] for file in files),
        "provisional_schemas": sorted(reg.tentative),
    }
    if not paths:
        report["error"] = "no input files matched"
    for file in files:
        if "error" in file:
            print("BAD", file["path"], file["error"])
        for name, item in file["streams"].items():
            print("OK " if item["passed"] else "BAD", Path(file["path"]).name, name, {key: value for key, value in item.items() if key != "trace"})
            if args.verbose and "trace" in item:
                print(item["trace"])
    print(f"{report['passed_streams']}/{len(streams)} streams round-trip with no tail across {len(files)} files")
    if "error" in report:
        print(report["error"], file=sys.stderr)
    if args.report is not None:
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
