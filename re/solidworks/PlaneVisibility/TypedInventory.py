from collections.abc import Mapping
from functools import partial
from hashlib import sha256
import json

from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Config.ReadPartConfig import ReadPartConfig
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Definition.Fields.DefPrefixFields import (
    KDefPrefixFields,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefClsid import ReadDefClass
from convert.adapters.solidworks.Archive.Definition.ModelDefContext import (
    ModelDefContext,
)
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def digest(value):
    return sha256(value).hexdigest()


def descriptor(value):
    if type(value) is ExternalClass:
        return {"name": value.NameValue, "external_index": value.IndexValue}
    return {"name": value.NameValue, "schema": value.SchemaValue}


def inventory(root, snapshot):
    leaves, owners, seen = {}, {}, {}

    def visit(value, path):
        if isinstance(value, ArchiveNode):
            if id(value) in seen:
                leaves[path] = {"reference": seen[id(value)]}
                return
            seen[id(value)] = path
            owners[path] = {
                **descriptor(value.ClassValue),
                "index": value.IndexValue,
                "span": [value.StartOffset, value.EndOffset],
            }
            for key in sorted(value.FieldsValue):
                visit(
                    value.FieldsValue[key],
                    path + "/" + key.replace("~", "~0").replace("/", "~1"),
                )
        elif isinstance(value, Mapping):
            leaves[path] = {"mapping_count": len(value)}
            for key in sorted(value):
                if type(key) is not str:
                    raise TypeError("typed mapping has a non-string field key")
                visit(
                    value[key], path + "/" + key.replace("~", "~0").replace("/", "~1")
                )
        elif type(value) in (tuple, list):
            leaves[path] = {"sequence": type(value).__name__, "count": len(value)}
            for index, item in enumerate(value):
                visit(item, path + "/" + str(index))
        elif type(value) is bytes:
            leaves[path] = {"bytes": len(value), "sha256": digest(value)}
        elif type(value) is str:
            encoded = value.encode("utf-16-le", errors="surrogatepass")
            leaves[path] = {"utf16_units": len(encoded) // 2, "sha256": digest(encoded)}
        elif type(value) is float:
            leaves[path] = {"binary64": value.hex()}
        elif value is None or type(value) in (bool, int):
            leaves[path] = {"type": type(value).__name__, "value": value}
        elif type(value) in (RuntimeClass, ExternalClass):
            leaves[path] = {"class": descriptor(value)}
        else:
            raise TypeError("unhandled typed inventory value: " + type(value).__name__)

    visit(root, "root")
    slots = []
    for entry in sorted(snapshot.EntriesValue, key=lambda value: value.IndexValue):
        value = entry.EntryValue
        is_node = isinstance(value, ArchiveNode)
        slots.append(
            {
                "slot": entry.IndexValue,
                "kind": "object" if is_node else "class",
                **descriptor(value.ClassValue if is_node else value),
                "owner": seen.get(id(value)) if is_node else None,
            }
        )
    return {
        "owners": owners,
        "leaves": leaves,
        "map": {"next_index": snapshot.CounterValue, "slots": slots},
    }


def schema_definition(data, version):
    context = ModelDefContext(version)
    cursor = BinaryReader(data)
    reader = GraphReader(
        cursor, ArchiveMaps(1), partial(ReadBodyMut, context), RequireCanonicalTags=True
    )
    fields = {
        rule.NameValue: ReadScalarMut(cursor, rule.TypeValue)
        for rule in KDefPrefixFields
    }
    root = ArchiveNode(ReadDefClass(cursor.TakeBytes(16), Assembly=False), fields)
    ReadBodyMut(context, reader, root)
    if cursor.GetRemaining() != 0:
        raise ValueError("schema-only Definition has unconsumed bytes")
    return root, reader.MapValue.Snapshot(), context


def inspect(archive, version):
    results, full = {}, {}
    try:
        config = ReadPartConfig(archive)
        encoded, rewritten = WriteConfigMut(
            config.RootValue, version, config.HeaderValue
        )
        if encoded != archive.Require("Contents/Config-0"):
            raise ValueError("typed Config-0 re-emission differs")
        full["config"] = inventory(config.RootValue, config.MapValue)
        results["config"] = {
            "schema_complete": True,
            "exact_reemit": True,
            "version": config.VersionValue,
            "map_base": config.MapBase,
            "next_index": config.MapValue.CounterValue,
            "missing_schemas": config.ReportValue.get("missing_schemas"),
            "native_byte_fields": config.ReportValue.get("native_byte_fields"),
        }
    except (ValueError, TypeError, KeyError) as error:
        results["config"] = {"refused": type(error).__name__ + ": " + str(error)}
    data = archive.Require("Contents/Definition")
    try:
        ReadModelDef(data, version)
        results["definition_strict"] = {"admitted": True}
    except (ValueError, TypeError, KeyError) as error:
        results["definition_strict"] = {
            "admitted": False,
            "refused": type(error).__name__ + ": " + str(error),
        }
    try:
        root, snapshot, context = schema_definition(data, version)
        full["definition_schema_only"] = inventory(root, snapshot)
        results["definition_schema_only"] = {
            "all_bytes_consumed": True,
            "canonical_tags": True,
            "next_index": snapshot.CounterValue,
            "missing_schemas": sorted(context.UsageValue.MissingNames),
            "production_scope_checked": False,
        }
    except (ValueError, TypeError, KeyError) as error:
        results["definition_schema_only"] = {
            "refused": type(error).__name__ + ": " + str(error),
            "production_scope_checked": False,
        }
    return results, full


def compare(before, after):
    changed = {}
    for name in sorted(set(before) | set(after)):
        first, second = before.get(name), after.get(name)
        if first == second:
            continue
        if first is None or second is None:
            changed[name] = {
                "before_present": first is not None,
                "after_present": second is not None,
            }
            continue
        rows = []
        for section in ("owners", "leaves"):
            for path in sorted(set(first[section]) | set(second[section])):
                left, right = first[section].get(path), second[section].get(path)
                if left != right:
                    rows.append(
                        {
                            "section": section,
                            "path": path,
                            "before": left,
                            "after": right,
                        }
                    )
        changed[name] = {
            "rows": rows,
            "map_before": first["map"],
            "map_after": second["map"],
        }
    return changed
