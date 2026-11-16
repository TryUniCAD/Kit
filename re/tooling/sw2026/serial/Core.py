from __future__ import annotations

import struct

from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount
from convert.adapters.solidworks.Archive.Counts.ReadCount import ReadCount
from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag
from convert.adapters.solidworks.Archive.Tags.EncodeTag import EncodeTag
from convert.adapters.solidworks.Archive.Tags.ReadTag import ReadTag

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


class Obj:
    __slots__ = ("cls", "f", "schema", "pos", "end", "index")

    def __init__(self, cls, f=None, schema=1):
        self.cls = cls
        self.f = {} if f is None else f
        self.schema = schema
        self.pos = None
        self.end = None
        self.index = None

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
    __slots__ = ("count", "table")

    def __init__(self, count, table):
        if count < 1 or any(index < 1 or index >= count for index in table):
            raise ArchiveError("invalid archive map snapshot")
        self.count = count
        self.table = dict(table)


class Load:
    def __init__(self, data, base=1, registry=None, version=None, ctx=None, *, seed=None):
        if seed is not None and base != seed.count:
            raise ArchiveError("archive map seed does not match the stream base")
        self.b = bytes(data)
        self.p = 0
        self.count = base
        self.base = base
        self.table = {} if seed is None else dict(seed.table)
        self.registry = registry
        self.version = version
        self.ctx = ctx or {}
        self.trace = []

    def map_state(self):
        return ArchiveMap(self.count, self.table)

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
        n = self.prim("u8")
        unicode = False
        if n == 0xFF:
            w = self.prim("u16")
            if w == 0xFFFE:
                unicode = True
                n = self.prim("u8")
                if n == 0xFF:
                    n = self.prim("u16")
                    if n == 0xFFFF:
                        n = self.prim("u32")
            elif w == 0xFFFF:
                n = self.prim("u32")
            else:
                n = w
        if unicode:
            return self.raw(2 * n).decode("utf-16-le", "surrogatepass")
        return ("A", self.raw(n).decode("latin-1"))

    def read_class(self):
        try:
            tag, position = ReadTag(self.b, self.p)
        except (TypeError, ValueError) as error:
            raise ArchiveError(f"invalid archive tag at {self.p}: {error}") from error
        self.p = position
        if tag.KindValue == "Null":
            return ("null", None)
        if tag.KindValue == "NewClass":
            schema = self.prim("u16")
            n = self.prim("u16")
            name = self.raw(n).decode("latin-1")
            idx = self.count
            self.table[idx] = ("class", name, schema)
            self.count += 1
            return ("classdef", (name, schema))
        return ("classref" if tag.KindValue == "ClassRef" else "objref", tag.IndexValue)

    def cls(self):
        pos = self.p
        kind, v = self.read_class()
        if kind == "null":
            return None
        if kind == "classdef":
            return v
        if kind == "classref":
            ent = self.table.get(v)
            if ent is None or ent[0] != "class":
                raise ArchiveError(f"bad class ref {v} at {pos}")
            return (ent[1], ent[2])
        raise ArchiveError(f"expected class tag at {pos}")

    def obj(self, expect=None):
        pos = self.p
        kind, v = self.read_class()
        if kind == "null":
            return None
        if kind == "objref":
            ent = self.table.get(v)
            if ent is None and v < self.base:
                return ExtRef(v)
            if ent is None or ent[0] != "obj":
                raise ArchiveError(f"bad object ref {v} at {pos}")
            return ent[1]
        if kind == "classdef":
            name, schema = v
        else:
            ent = self.table.get(v)
            if ent is None or ent[0] != "class":
                raise ArchiveError(f"bad class ref {v} at {pos}")
            name, schema = ent[1], ent[2]
        o = Obj(name, schema=schema)
        o.pos = pos
        o.index = self.count
        self.table[self.count] = ("obj", o)
        self.count += 1
        self.registry.load(self, o)
        o.end = self.p
        return o


class Store:
    def __init__(self, base=1, registry=None, version=None, ctx=None, *, seed=None):
        if seed is not None and base != seed.count:
            raise ArchiveError("archive map seed does not match the stream base")
        self.out = bytearray()
        self.count = base
        self.base = base
        self.classes = {}
        self.objects = {}
        self.nodes = {}
        if seed is not None:
            for index, entry in seed.table.items():
                if entry[0] == "class":
                    self.classes[(entry[1], entry[2])] = index
                elif entry[0] == "obj":
                    node = entry[1]
                    self.objects[id(node)] = index
                    self.nodes[id(node)] = node
                else:
                    raise ArchiveError(f"unknown archive map entry {entry[0]!r}")
        self.registry = registry
        self.version = version
        self.ctx = ctx or {}

    def map_state(self):
        table = {index: ("class", name, schema) for (name, schema), index in self.classes.items()}
        for key, index in self.objects.items():
            if index in table:
                raise ArchiveError(f"duplicate archive map index {index}")
            table[index] = ("obj", self.nodes[key])
        return ArchiveMap(self.count, table)

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
        if isinstance(s, tuple):
            data = s[1].encode("latin-1")
            n = len(data)
            if n < 0xFF:
                self.prim("u8", n)
            elif n < 0xFFFE:
                self.prim("u8", 0xFF)
                self.prim("u16", n)
            else:
                self.prim("u8", 0xFF)
                self.prim("u16", 0xFFFF)
                self.prim("u32", n)
            self.raw(data)
            return
        data = s.encode("utf-16-le", "surrogatepass")
        n = len(data) // 2
        self.prim("u8", 0xFF)
        self.prim("u16", 0xFFFE)
        if n < 0xFF:
            self.prim("u8", n)
        elif n < 0xFFFE:
            self.prim("u8", 0xFF)
            self.prim("u16", n)
        else:
            self.prim("u8", 0xFF)
            self.prim("u16", 0xFFFF)
            self.prim("u32", n)
        self.raw(data)

    def tag(self, idx, cls):
        try:
            self.out.extend(EncodeTag(ArchiveTag("ClassRef" if cls else "ObjectRef", idx)))
        except (TypeError, ValueError) as error:
            raise ArchiveError(f"invalid archive reference tag: {error}") from error

    def cls(self, c):
        if c is None:
            self.out.extend(EncodeTag(ArchiveTag("Null", None)))
            return
        name, schema = c
        if (name, schema) in self.classes:
            self.tag(self.classes[(name, schema)], True)
            return
        self.out.extend(EncodeTag(ArchiveTag("NewClass", None)))
        self.prim("u16", schema)
        raw = name.encode("latin-1")
        self.prim("u16", len(raw))
        self.raw(raw)
        self.classes[(name, schema)] = self.count
        self.count += 1

    def obj(self, o):
        if o is None:
            self.cls(None)
            return
        if isinstance(o, ExtRef):
            self.tag(o.index, False)
            return
        key = id(o)
        if key in self.objects:
            self.tag(self.objects[key], False)
            return
        self.cls((o.cls, o.schema))
        self.objects[key] = self.count
        self.nodes[key] = o
        self.count += 1
        self.registry.store(self, o)
