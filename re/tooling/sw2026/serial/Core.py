from __future__ import annotations

import struct

from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount
from convert.adapters.solidworks.Archive.Counts.ReadCount import ReadCount
from convert.adapters.solidworks.Archive.Maps.AddEntryMut import AddEntryMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.BindClassMut import BindClassMut
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.ExternalRef import ExternalRef
from convert.adapters.solidworks.Archive.Objects.ObjectRead import ObjectRead
from convert.adapters.solidworks.Archive.Objects.ObjectStore import ObjectStore
from convert.adapters.solidworks.Archive.Objects.ReadClassMut import ReadClassMut
from convert.adapters.solidworks.Archive.Objects.ReadObjectMut import ReadObjectMut
from convert.adapters.solidworks.Archive.Objects.ReadTypeMut import ReadTypeMut
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Objects.WriteClassMut import WriteClassMut
from convert.adapters.solidworks.Archive.Objects.WriteObjectMut import WriteObjectMut
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Archive.Strings.EncodeString import EncodeString
from convert.adapters.solidworks.Archive.Strings.ReadString import ReadString
from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag
from convert.adapters.solidworks.Archive.Tags.EncodeTag import EncodeTag
from convert.adapters.solidworks.Archive.Tags.ReadTag import ReadTag
from MapBridge import MapTable, class_value, legacy_entry, schema_value, typed_snapshot

NULL_TAG = 0x0000
NEW_CLASS = 0xFFFF
CLASS_TAG = 0x8000
BIG_TAG = 0x7FFF
BIG_CLASS = 0x80000000

PRIMS = {
    "u8": "<B", "i8": "<b", "u16": "<H", "i16": "<h", "u32": "<I", "i32": "<i",
    "u64": "<Q", "i64": "<q", "f32": "<f", "f64": "<d",
}


class ArchiveError(Exception):
    pass


class Obj(ArchiveNode):
    __slots__ = ()

    def __init__(self, cls, f=None, schema=1):
        super().__init__(class_value(cls, schema), {} if f is None else f)

    cls = property(lambda self: self.ClassValue.NameValue, lambda self, value: setattr(self, "ClassValue", class_value(value, self.schema)))
    schema = property(lambda self: schema_value(self.ClassValue))
    f = property(lambda self: self.FieldsValue, lambda self, value: setattr(self, "FieldsValue", value))
    pos = property(lambda self: self.StartOffset, lambda self, value: setattr(self, "StartOffset", value))
    end = property(lambda self: self.EndOffset, lambda self, value: setattr(self, "EndOffset", value))
    index = property(lambda self: self.IndexValue, lambda self, value: setattr(self, "IndexValue", value))

    def __getitem__(self, k):
        return self.f[k]

    def __setitem__(self, k, v):
        self.f[k] = v

    def get(self, k, d=None):
        return self.f.get(k, d)

    def __repr__(self):
        return f"<{self.cls} {self.f!r}>"


class ExtRef:
    __slots__ = ("index",)

    def __init__(self, index):
        self.index = index

    def __repr__(self):
        return f"<ext {self.index}>"


class ArchiveMap:
    __slots__ = ("state",)

    def __init__(self, count=None, table=None, *, snapshot=None):
        if snapshot is not None:
            if count is not None or table is not None or type(snapshot) is not MapSnapshot:
                raise ArchiveError("invalid archive map snapshot arguments")
            self.state = snapshot
        else:
            self.state = typed_snapshot(count, table)

    count = property(lambda self: self.state.CounterValue)
    table = property(lambda self: {entry.IndexValue: legacy_entry(entry.EntryValue) for entry in self.state.EntriesValue})


class ArchiveState:
    def setup_maps(self, base, seed):
        self._maps = ArchiveMaps(base, None if seed is None else seed.state)

    @property
    def count(self):
        return self._maps.CounterValue

    @count.setter
    def count(self, value):
        snapshot = MapSnapshot(value, tuple(self._maps.EntryMap.values()))
        if value < self._maps.BaseValue:
            raise ArchiveError("archive counter cannot precede its inherited prefix")
        self._maps.CounterValue = snapshot.CounterValue

    @property
    def base(self):
        return self._maps.BaseValue

    @base.setter
    def base(self, value):
        if type(value) is not int or not 1 <= value <= self.count:
            raise ArchiveError("archive base is outside its current map")
        self._maps.BaseValue = value

    @property
    def table(self):
        return MapTable(self._maps)

    @table.setter
    def table(self, value):
        base = self.base
        self._maps = ArchiveMaps(self.count, typed_snapshot(self.count, value))
        self._maps.BaseValue = base

    def map_state(self):
        return ArchiveMap(snapshot=self._maps.Snapshot())

    def bind_class(self, index, name):
        BindClassMut(self._maps, ExternalClass(name, index))


class Load(ArchiveState):
    def __init__(self, data, base=1, registry=None, version=None, ctx=None, *, seed=None):
        if seed is not None and base != seed.count:
            raise ArchiveError("archive map seed does not match the stream base")
        self.b = bytes(data)
        self.p = 0
        self.setup_maps(base, seed)
        self.registry = registry
        self.version = version
        self.ctx = ctx or {}
        self.trace = []

    def left(self):
        return len(self.b) - self.p

    def prim(self, kind):
        fmt = PRIMS[kind]
        n = struct.calcsize(fmt)
        if self.p + n > len(self.b):
            raise ArchiveError(f"eof reading {kind} at {self.p}")
        v = struct.unpack_from(fmt, self.b, self.p)[0]
        self.p += n
        return v

    def raw(self, n):
        if n < 0 or self.p + n > len(self.b):
            raise ArchiveError(f"eof reading {n} bytes at {self.p}")
        v = self.b[self.p:self.p + n]
        self.p += n
        return v

    def count_value(self, *, framework=False):
        try:
            value, position = ReadCount(self.b, self.p, IsFramework=framework)
        except (TypeError, ValueError) as error:
            raise ArchiveError(f"invalid archive count at {self.p}: {error}") from error
        self.p = position
        return value

    def string(self):
        try:
            value, position = ReadString(self.b, self.p)
        except (TypeError, ValueError) as error:
            raise ArchiveError(f"invalid archive string at {self.p}: {error}") from error
        self.p = position
        return value.TextValue if value.IsUnicode else ("A", value.TextValue)

    def read_tag(self):
        try:
            tag, position = ReadTag(self.b, self.p)
        except (TypeError, ValueError) as error:
            raise ArchiveError(f"invalid archive tag at {self.p}: {error}") from error
        self.p = position
        return tag

    def read_descriptor(self):
        schema = self.prim("u16")
        length = self.prim("u16")
        return RuntimeClass(self.raw(length).decode("latin-1"), schema)

    def object_reader(self):
        return ObjectRead(
            self._maps, self.read_tag, self.read_descriptor,
            lambda node: self.registry.load(self, node),
            lambda descriptor: Obj(descriptor.NameValue, schema=schema_value(descriptor)),
            lambda: self.p,
        )

    def read_class(self):
        tag = self.read_tag()
        if tag.KindValue == "Null":
            return ("null", None)
        if tag.KindValue == "NewClass":
            descriptor = ReadTypeMut(self.object_reader(), tag)
            return ("classdef", (descriptor.NameValue, schema_value(descriptor)))
        return ("classref" if tag.KindValue == "ClassRef" else "objref", tag.IndexValue)

    def cls(self):
        try:
            descriptor = ReadClassMut(self.object_reader())
            return None if descriptor is None else (descriptor.NameValue, schema_value(descriptor))
        except (TypeError, ValueError) as error:
            raise ArchiveError(f"invalid archive class at {self.p}: {error}") from error

    def obj(self, expect=None):
        try:
            value = ReadObjectMut(self.object_reader())
            return ExtRef(value.IndexValue) if type(value) is ExternalRef else value
        except (TypeError, ValueError) as error:
            raise ArchiveError(f"invalid archive object at {self.p}: {error}") from error


class Store(ArchiveState):
    def __init__(self, base=1, registry=None, version=None, ctx=None, *, seed=None):
        if seed is not None and base != seed.count:
            raise ArchiveError("archive map seed does not match the stream base")
        self.out = bytearray()
        self.setup_maps(base, seed)
        self.registry = registry
        self.version = version
        self.ctx = ctx or {}

    @property
    def classes(self):
        return {(descriptor.NameValue, schema_value(descriptor)): index for descriptor, index in self._maps.ClassLookup.items()}

    @property
    def objects(self):
        return self._maps.ObjectLookup

    @property
    def nodes(self):
        return {id(entry.EntryValue): entry.EntryValue for entry in self._maps.EntryMap.values() if isinstance(entry.EntryValue, ArchiveNode)}

    def prim(self, kind, v):
        self.out += struct.pack(PRIMS[kind], v)

    def raw(self, v):
        self.out += v

    def count_value(self, v, *, framework=False):
        try:
            self.out.extend(EncodeCount(v, IsFramework=framework))
        except (TypeError, ValueError) as error:
            raise ArchiveError(f"invalid archive count: {error}") from error

    def string(self, s):
        try:
            if type(s) is tuple and len(s) == 2 and s[0] == "A":
                value = CStringValue(s[1], False)
            elif type(s) is str:
                value = CStringValue(s, True)
            else:
                raise TypeError("archive strings require Unicode text or an ANSI text pair")
            self.out.extend(EncodeString(value, IsSourceFrame=True))
        except (TypeError, ValueError) as error:
            raise ArchiveError(f"invalid archive string: {error}") from error

    def tag(self, idx, cls):
        try:
            self.out.extend(EncodeTag(ArchiveTag("ClassRef" if cls else "ObjectRef", idx)))
        except (TypeError, ValueError) as error:
            raise ArchiveError(f"invalid archive reference tag: {error}") from error

    def write_tag(self, tag):
        self.out.extend(EncodeTag(tag))

    def write_descriptor(self, descriptor):
        self.prim("u16", descriptor.SchemaValue)
        raw = descriptor.NameValue.encode("latin-1")
        self.prim("u16", len(raw))
        self.raw(raw)

    def object_writer(self):
        return ObjectStore(self._maps, self.write_tag, self.write_descriptor, lambda node: self.registry.store(self, node))

    def cls(self, c):
        try:
            WriteClassMut(self.object_writer(), None if c is None else class_value(*c))
        except (TypeError, ValueError) as error:
            raise ArchiveError(f"invalid archive class: {error}") from error

    def obj(self, o):
        try:
            WriteObjectMut(self.object_writer(), ExternalRef(o.index) if isinstance(o, ExtRef) else o)
        except (TypeError, ValueError) as error:
            raise ArchiveError(f"invalid archive object: {error}") from error
