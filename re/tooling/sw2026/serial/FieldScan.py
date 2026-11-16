from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.container.Container import SldprtArchive
from Core import Obj, ExtRef
import Streams
import Classes
import RoundTrip


def walk(v, path, out, seen, owner):
    if isinstance(v, Obj):
        if id(v) in seen:
            out[(owner, path)].append(("ref", v.cls))
            return
        seen.add(id(v))
        for k, x in v.f.items():
            walk(x, k, out, seen, v.cls)
        return
    if isinstance(v, ExtRef):
        out[(owner, path)].append(("ext", v.index))
        return
    if isinstance(v, dict):
        for k, x in v.items():
            walk(x, f"{path}.{k}", out, seen, owner)
        return
    if isinstance(v, list):
        out[(owner, path + "#n")].append(len(v))
        for i, x in enumerate(v):
            walk(x, f"{path}[]", out, seen, owner)
        return
    if isinstance(v, bytes):
        out[(owner, path)].append(("bytes", len(v)))
        return
    out[(owner, path)].append(v)


def load(name, data, reg, archive, plans):
    kind, base = RoundTrip.plan(name, plans)
    if kind == "resolved":
        return Streams.load_resolved(data, reg, 19000)[0]
    if kind == "custom":
        return base[0](data, reg, 19000, archive=archive, name=name)[0]
    return Streams.load_rooted(data, reg, base, 19000)[0]


def fingerprint(data):
    return hashlib.sha256(data).hexdigest()


def integer(value):
    return {"type": "int", "value": value, "decimal": str(value)}


class FieldInventory:
    def __init__(self):
        self.identities = {}
        self.nodes = []
        self.origins = {}
        self.references = []
        self.keepalive = []

    def register_map(self, ar, stream):
        for index, entry in ar.table.items():
            if entry[0] == "obj":
                self.origins.setdefault(id(entry[1]), {"stream": stream, "archive_index": integer(index)})

    def value(self, value, stream, path, owner=None):
        context = {"stream": stream, "path": path, "owner_object": owner}
        if value is None:
            return {"type": "null", "value": None, "context": context}
        if isinstance(value, bool):
            return {"type": "bool", "value": value, "context": context}
        if isinstance(value, int):
            return {**integer(value), "context": context}
        if isinstance(value, float):
            return {
                "type": "float", "value": value if math.isfinite(value) else value.hex(),
                "hex": value.hex(), "finite": math.isfinite(value), "context": context,
                "decoded_python_binary64_be": struct.pack(">d", value).hex(),
            }
        if isinstance(value, str):
            return {"type": "str", "value": value, "context": context}
        if isinstance(value, (bytes, bytearray, memoryview)):
            raw = bytes(value)
            return {"type": "bytes", "bytes": len(raw), "sha256": fingerprint(raw), "context": context}
        if isinstance(value, ExtRef):
            reference = {
                "type": "external-object-reference", "archive_index": integer(value.index),
                "resolution": "unresolved", "target_id": None, "context": context,
            }
            self.references.append(reference)
            return reference
        if not isinstance(value, (Obj, dict, list, tuple)):
            raise TypeError(f"unsupported inventory value type: {type(value).__module__}.{type(value).__qualname__}")
        identity = self.identities.get(id(value))
        if identity is not None:
            reference = {"type": "reference", "target_id": identity, "context": context}
            self.references.append(reference)
            return reference
        identity = f"node-{len(self.nodes) + 1}"
        self.identities[id(value)] = identity
        self.keepalive.append(value)
        kind = "object" if isinstance(value, Obj) else "dict" if isinstance(value, dict) else "list" if isinstance(value, list) else "tuple"
        node = {"id": identity, "type": kind, "first_seen": context}
        self.nodes.append(node)
        reference = {"type": "reference", "target_id": identity, "context": context}
        self.references.append(reference)
        if isinstance(value, Obj):
            origin = self.origins.get(id(value))
            origin_stream = origin["stream"] if origin is not None else stream
            node.update({
                "class": value.cls,
                "schema": self.value(value.schema, origin_stream, path + ["schema"], identity),
                "archive_origin": origin,
                "archive_index": integer(value.index) if value.index is not None else None,
                "record_start": value.pos, "record_end": value.end,
                "position_stream": origin_stream if value.pos is not None else None,
                "field_count": len(value.f),
                "fields": [{
                    "name": self.value(key, origin_stream, path + ["fields", index, "name"], identity),
                    "value": self.value(item, origin_stream, path + ["fields", index, "value"], identity),
                } for index, (key, item) in enumerate(value.f.items())],
            })
        elif isinstance(value, dict):
            node.update({
                "length": len(value),
                "entries": [{
                    "key": self.value(key, stream, path + [index, "key"], owner),
                    "value": self.value(item, stream, path + [index, "value"], owner),
                } for index, (key, item) in enumerate(value.items())],
            })
        else:
            node.update({
                "length": len(value),
                "items": [self.value(item, stream, path + [index], owner) for index, item in enumerate(value)],
            })
        return reference

    def document(self, name, doc, ar):
        self.register_map(ar, name)
        return {
            "stream": name, "map_base": integer(ar.base), "map_count": integer(ar.count),
            "head": self.value(doc.head, name, ["head"]),
            "roots": self.value(doc.roots, name, ["roots"]),
            "loader_context": self.value(ar.ctx, name, ["loader_context"]),
            "archive_map": [{
                "index": integer(index), "kind": entry[0],
                "value": self.value(entry[1] if entry[0] == "obj" else entry, name, ["archive_map", index]),
            } for index, entry in sorted(ar.table.items())],
        }


def inventory_load(name, data, reg, archive, plans, linked, record):
    kind, framing = RoundTrip.plan(name, plans)
    dependencies = []
    options = {}
    usage = None
    try:
        with reg.track_usage("load", name, role="field_inventory", sources=archive.streams) as usage:
            if linked:
                if not name.endswith("-ResolvedFeatures") or kind != "custom":
                    raise ValueError("linked inventory requires a custom resolved-features stream plan")
                from defs.ConfigPart import load_config
                configuration_name = name.removesuffix("-ResolvedFeatures")
                configuration_data = archive.require(configuration_name)
                with reg.track_usage("load", configuration_name, role="linked_map_seed", sources=archive.streams) as dependency:
                    entry = {"name": configuration_name, "data": configuration_data, "usage": dependency}
                    dependencies.append(entry)
                    configuration, configuration_ar = load_config(configuration_data, reg, 19000, archive=archive, name=configuration_name)
                    entry["tail"] = len(configuration.tail)
                    if configuration.tail:
                        raise ValueError("linked configuration has an unread tail")
                    entry.update(doc=configuration, archive=configuration_ar)
                options["seed"] = configuration_ar.map_state()
            if kind == "resolved":
                doc, ar = Streams.load_resolved(data, reg, 19000)
            elif kind == "custom":
                doc, ar = framing[0](data, reg, 19000, archive=archive, name=name, **options)
            elif kind == "rooted":
                doc, ar = Streams.load_rooted(data, reg, framing, 19000)
            else:
                raise ValueError("unsupported field-inventory stream plan")
            record["stream"]["tail"] = len(doc.tail)
            if doc.tail:
                record["stream"]["tail_sha256"] = fingerprint(doc.tail)
                raise ValueError("selected inventory stream has an unread tail")
        return doc, ar, dependencies
    finally:
        record["schema_usage"] = {
            "load": usage.snapshot() if usage is not None else None,
            "dependencies": [{
                **item["usage"].snapshot(), "bytes": len(item["data"]),
                "sha256": fingerprint(item["data"]), "tail": item.get("tail"),
            } for item in dependencies],
        }


def inventory_file(path, name, linked, require_proven):
    record = {"path": str(path), "name": Path(path).name, "passed": False, "stage": "read_file", "stream": {"name": name}}
    try:
        raw = Path(path).read_bytes()
        record.update(bytes=len(raw), sha256=fingerprint(raw))
        record["stage"] = "container"
        archive = SldprtArchive.from_bytes(raw, path)
        versions = {key.split("/", 1)[0] for key in archive.streams if key.startswith("_MO_VERSION_")}
        if versions != {"_MO_VERSION_19000"}:
            raise ValueError("field inventory requires native document version 19000")
        data = archive.require(name)
        record["stream"].update(bytes=len(data), sha256=fingerprint(data))
        reg = Classes.registry()
        plans = {**RoundTrip.PLANS, **reg.plans}
        record["stage"] = "archive_load"
        doc, ar, dependencies = inventory_load(name, data, reg, archive, plans, linked, record)
        snapshots = [record["schema_usage"]["load"], *record["schema_usage"]["dependencies"]]
        record["proven_schemas"] = all(item["completed"] and not item["provisional_schemas"] and not item["missing_schemas"] for item in snapshots)
        if require_proven and not record["proven_schemas"]:
            raise ValueError("field inventory reached provisional or missing schemas")
        record["stage"] = "field_graph"
        inventory = FieldInventory()
        dependency_records = []
        for item in dependencies:
            dependency_records.append({
                "name": item["name"], "bytes": len(item["data"]), "sha256": fingerprint(item["data"]),
                "tail": len(item["doc"].tail), "role": "linked_map_seed",
                "document": inventory.document(item["name"], item["doc"], item["archive"]),
            })
        record["document"] = inventory.document(name, doc, ar)
        record["dependencies"] = dependency_records
        record["nodes"] = inventory.nodes
        record["node_count"] = len(inventory.nodes)
        record["reference_count"] = len(inventory.references)
        record["unresolved_reference_count"] = sum(item["type"] == "external-object-reference" for item in inventory.references)
        record["stream"]["tail"] = len(doc.tail)
        source_names = sorted({candidate for snapshot in snapshots for call in snapshot["schema_calls"] for candidate in call["source_streams"]})
        record["loader_source_streams"] = [{
            "name": candidate, "bytes": len(archive.require(candidate)), "sha256": fingerprint(archive.require(candidate)),
            "graph_included": candidate == name or any(candidate == item["name"] for item in dependencies),
        } for candidate in source_names]
        record["passed"] = True
        record["stage"] = "complete"
    except Exception as error:
        record["error"] = {
            "type": f"{type(error).__module__}.{type(error).__qualname__}",
            "message_sha256": fingerprint(str(error).encode("utf-8", errors="surrogatepass")),
            "message_policy": "hashed to avoid dumping opaque payloads through codec exceptions",
        }
    return record


def inventory_main():
    parser = argparse.ArgumentParser(description="Remote-only complete decoded field inventory; no writer or byte-identity claim")
    parser.add_argument("pattern")
    parser.add_argument("stream")
    parser.add_argument("--inventory-json", type=Path, required=True)
    parser.add_argument("--link-config", action="store_true")
    parser.add_argument("--require-proven", action="store_true")
    args = parser.parse_args()
    if args.inventory_json.exists() or args.inventory_json.is_symlink() or not args.inventory_json.parent.is_dir():
        parser.error("inventory destination must be new and its parent must exist")
    files = sorted({path for path in glob.glob(args.pattern, recursive=True) if Path(path).is_file() and not Path(path).name.startswith("~$")})
    if any(Path(path).is_symlink() for path in files):
        parser.error("inventory inputs must not be symlinks")
    records = [inventory_file(path, args.stream, args.link_config, args.require_proven) for path in files]
    report = {
        "schema": "kit.sw2026.field-inventory.v1", "version": 19000,
        "purpose": "discovery/control correlation of decoded model fields",
        "scalar_type_scope": "decoded Python values; no inferred native scalar wire width or field byte offset",
        "graph_scope": "retained document head, roots, loader context and archive map, plus explicit linked configuration graph",
        "integer_encoding": "exact JSON integer plus authoritative decimal text",
        "field_classification": "unclassified; correlations are not construction rules or writer defaults",
        "raw_payloads_emitted": False, "values_truncated": False,
        "writer_output": False, "byte_roundtrip_performed": False, "native_acceptance": "unmeasured",
        "linked_configurations": args.link_config, "require_proven": args.require_proven,
        "file_count": len(records), "files": records,
        "implementation": [{
            "file": str(path.relative_to(ROOT)), "sha256": fingerprint(path.read_bytes()),
        } for path in [
            HERE / "FieldScan.py", HERE / "Core.py", HERE / "Schema.py", HERE / "Classes.py",
            HERE / "Streams.py", HERE / "RoundTrip.py", HERE / "Dsl.py", HERE / "AnnotationWire.py",
            HERE / "MapBridge.py",
            *sorted((HERE / "defs").glob("*.py")),
            ROOT / "src/convert/adapters/solidworks/Archive/Counts/EncodeCount.py",
            ROOT / "src/convert/adapters/solidworks/Archive/Counts/ReadCount.py",
            ROOT / "src/convert/adapters/solidworks/Archive/Strings/CStringValue.py",
            ROOT / "src/convert/adapters/solidworks/Archive/Strings/EncodeString.py",
            ROOT / "src/convert/adapters/solidworks/Archive/Strings/ReadLength.py",
            ROOT / "src/convert/adapters/solidworks/Archive/Strings/ReadString.py",
            ROOT / "src/convert/adapters/solidworks/Archive/Tags/ArchiveTag.py",
            ROOT / "src/convert/adapters/solidworks/Archive/Tags/EncodeTag.py",
            ROOT / "src/convert/adapters/solidworks/Archive/Tags/ReadTag.py",
            *[path for folder in ("Maps", "Objects") for path in sorted((ROOT / "src/convert/adapters/solidworks/Archive" / folder).glob("*.py"))],
        ]],
        "passed": bool(records) and all(item["passed"] for item in records),
    }
    if not records:
        report["error"] = "no input files matched"
    with args.inventory_json.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2, ensure_ascii=True, allow_nan=False)
        output.write("\n")
    print(json.dumps({"schema": report["schema"], "file_count": len(records), "passed": report["passed"]}))
    return 0 if report["passed"] else 1


def main():
    if any(argument == "--inventory-json" or argument.startswith("--inventory-json=") for argument in sys.argv[1:]):
        return inventory_main()
    pattern, name = sys.argv[1], sys.argv[2]
    reg = Classes.registry()
    plans = {**RoundTrip.PLANS, **reg.plans}
    per = {}
    files = sorted(p for p in glob.glob(pattern) if not Path(p).name.startswith("~$"))
    for path in files:
        archive = SldprtArchive.open(path)
        data = archive.get(name)
        if data is None:
            raise ValueError(f"required stream is missing: {name} in {path}")
        doc = load(name, data, reg, archive, plans)
        if doc.tail:
            raise ValueError(f"unread bytes in {name} in {path}: {len(doc.tail)}")
        out = collections.defaultdict(list)
        seen = set()
        for r in doc.roots:
            walk(r, "root", out, seen, "<stream>")
        walk(doc.head, "head", out, seen, "<stream>")
        per[Path(path).stem] = out
    if not per:
        raise ValueError("no input files matched")
    keys = sorted({k for o in per.values() for k in o}, key=lambda k: (k[0], k[1]))
    rows = []
    for k in keys:
        vals = {f: tuple(map(repr, o.get(k, []))) for f, o in per.items()}
        distinct = sorted(set(vals.values()))
        rows.append({"cls": k[0], "field": k[1], "distinct": len(distinct), "values": {f: list(v)[:6] for f, v in vals.items()} if len(distinct) > 1 else list(distinct[0])[:6]})
    if "--json" in sys.argv:
        print(json.dumps(rows, indent=1))
        return
    for r in rows:
        v = r["values"]
        if r["distinct"] == 1:
            print(f"{r['cls']}.{r['field']}  sample-invariant  {v}")
        else:
            print(f"{r['cls']}.{r['field']}  vary({r['distinct']})")
            for f, x in v.items():
                print(f"    {f}: {x}")


if __name__ == "__main__":
    raise SystemExit(main())
