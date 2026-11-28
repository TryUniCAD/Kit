from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Maps.MapEntry import MapEntry
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


def class_value(name, schema):
    if type(schema) is tuple and len(schema) == 2 and schema[0] == "ext":
        return ExternalClass(name, schema[1])
    return RuntimeClass(name, schema)


def schema_value(descriptor):
    if isinstance(descriptor, ExternalClass):
        return ("ext", descriptor.IndexValue)
    return descriptor.SchemaValue


def legacy_entry(entry):
    if isinstance(entry, (RuntimeClass, ExternalClass)):
        return ("class", entry.NameValue, schema_value(entry))
    return ("obj", ArchiveNode.RequireNode(entry))


def typed_snapshot(counter, table):
    entries = []
    for index, value in table.items():
        if value[0] == "class":
            entry = class_value(value[1], value[2])
        elif value[0] == "obj":
            entry = ArchiveNode.RequireNode(value[1])
        else:
            raise ValueError(f"unknown archive map entry {value[0]!r}")
        entries.append(MapEntry(index, entry))
    return MapSnapshot(counter, tuple(entries))


def legacy_row(entry, rows):
    key = id(entry)
    if key not in rows:
        rows[key] = (entry, legacy_entry(entry.EntryValue))
    return rows[key][1]


class MapTable(Mapping):
    def __init__(self, state, rows):
        self.state = state
        self.rows = rows

    def __getitem__(self, index):
        return legacy_row(self.state.EntryMap[index], self.rows)

    def __iter__(self):
        return iter(self.state.EntryMap)

    def __len__(self):
        return len(self.state.EntryMap)
