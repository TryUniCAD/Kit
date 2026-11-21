from collections import deque
from collections.abc import Mapping
from struct import pack

from SpatialTextMut import require
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


def node_class(node):
    require(
        type(node.ClassValue) is RuntimeClass,
        "linked comparison excludes unresolved external class placeholders",
    )
    return [node.ClassValue.NameValue, node.ClassValue.SchemaValue]


def object_paths(roots, anchors=None):
    labels = dict(anchors or {})
    nodes = {}
    queue = deque(roots)
    visited = 0
    while queue:
        path, value = queue.popleft()
        visited += 1
        require(visited <= 100000, "linked metadata traversal exceeds its finite scope")
        if type(value) is ArchiveNode:
            if id(value) in labels:
                continue
            labels[id(value)] = path
            nodes[path] = value
            node_class(value)
            queue.append((path + "/fields", value.FieldsValue))
        elif isinstance(value, Mapping):
            require(
                all(type(key) is str for key in value), "linked field keys are not text"
            )
            queue.extend((path + "/" + key, value[key]) for key in sorted(value))
        elif type(value) in (tuple, list):
            queue.extend(
                (path + "/" + str(index), item) for index, item in enumerate(value)
            )
    return labels, nodes


def scalar(value, labels):
    if type(value) is ArchiveNode:
        require(id(value) in labels, "linked reference has no actual graph identity")
        return {"reference": labels[id(value)]}
    if isinstance(value, Mapping):
        return {key: scalar(value[key], labels) for key in sorted(value)}
    if type(value) in (list, tuple):
        return {
            "collection": type(value).__name__,
            "items": [scalar(item, labels) for item in value],
        }
    if type(value) is CStringValue:
        return {"cstring": value.TextValue, "unicode": value.IsUnicode}
    if type(value) is float:
        return {"float64": pack("<d", value).hex()}
    if type(value) is bytes:
        return {"bytes": value.hex()}
    if value is None or type(value) in (str, int, bool):
        return value
    raise TypeError("unrepresented linked field type " + type(value).__name__)


def linked_state(child):
    config, resolved = child.ConfigValue, child.ResolvedValue
    anchors, seed_nodes = object_paths(
        (("header", config.HeaderValue), ("config", config.RootValue))
    )
    inherited = {
        entry.IndexValue: entry.EntryValue for entry in resolved.MapValue.EntriesValue
    }
    seed_objects = {}
    seed_classes = []
    for entry in config.MapValue.EntriesValue:
        require(
            inherited.get(entry.IndexValue) is entry.EntryValue,
            "resolved loading did not retain the exact configuration seed alias",
        )
        node = entry.EntryValue
        if type(node) is RuntimeClass:
            seed_classes.append([node.NameValue, node.SchemaValue])
        else:
            require(
                type(node) is ArchiveNode and id(node) in anchors,
                "configuration map has an unowned seeded object",
            )
            seed_objects[anchors[id(node)]] = node_class(node)
    labels, nodes = object_paths(
        (("roots", resolved.RootsValue), ("extra", resolved.ExtraFields)), anchors
    )
    graph = {
        "roots": scalar(resolved.RootsValue, labels),
        "extra": scalar(resolved.ExtraFields, labels),
        "context": dict(resolved.ContextValue),
        "objects": {
            path: {
                "class": node_class(node),
                "fields": scalar(node.FieldsValue, labels),
            }
            for path, node in sorted(nodes.items())
        },
    }
    require(
        resolved.MapBase == config.MapValue.CounterValue,
        "resolved stream does not begin at the actual configuration counter",
    )
    return {
        "config_counter": config.MapValue.CounterValue,
        "resolved_counter": resolved.MapValue.CounterValue,
        "resolved_base": resolved.MapBase,
        "seed_classes": sorted(seed_classes),
        "seed_objects": seed_objects,
        "resolved_graph": graph,
        "inherited_aliases_preserved": True,
    }
