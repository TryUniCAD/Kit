from __future__ import annotations

from collections import Counter
from contextlib import contextmanager

from Core import ArchiveError, Obj


class Usage:
    def __init__(self, registry, direction, stream, role, sources):
        self.registry = registry
        self.direction, self.stream, self.role = direction, stream, role
        self.sources = {} if sources is None else sources
        self.used, self.missing = set(), set()
        self.calls = Counter()
        self.schemas, self.operations, self.raw_operations = [], [], []
        self.archive_sources = {}
        self.completed = False

    def object_context(self, o):
        cls = o.cls if isinstance(o, Obj) else None
        return cls, f"{type(o).__module__}.{type(o).__qualname__}"

    def source_streams(self, ar):
        if ar not in self.archive_sources:
            if not hasattr(ar, "b"):
                matches = [self.stream]
            else:
                matches = [name for name, data in self.sources.items() if data is ar.b]
                if not matches:
                    matches = [name for name, data in self.sources.items() if data == ar.b]
            self.archive_sources[ar] = tuple(sorted(matches))
        return self.archive_sources[ar]

    @contextmanager
    def schema(self, name, ar, o, via):
        available = name in self.registry.classes
        (self.used if available else self.missing).add(name)
        parent = self.schemas[-1] if self.schemas else None
        cls, object_type = self.object_context(o)
        self.calls[(name, via, parent, cls, object_type, self.source_streams(ar))] += 1
        self.schemas.append(name)
        try:
            yield
        finally:
            self.schemas.pop()

    @contextmanager
    def operation(self, op, index, scope):
        self.operations.append({
            "operation": f"{type(op).__module__}.{type(op).__qualname__}",
            "index": index,
            "field": getattr(op, "name", None),
            "scope_index": getattr(scope, "index", None),
        })
        try:
            yield
        finally:
            self.operations.pop()

    def raw(self, op, ar, o, declared):
        if callable(op.n):
            code = getattr(op.n, "__code__", None)
            rule = {
                "kind": "callable",
                "module": getattr(op.n, "__module__", None),
                "name": getattr(op.n, "__qualname__", type(op.n).__qualname__),
                "source_file": getattr(code, "co_filename", None),
                "source_line": getattr(code, "co_firstlineno", None),
                "source": None,
                "source_status": "not read during archive execution",
            }
        else:
            rule = {"kind": "constant", "value": op.n}
        cls, object_type = self.object_context(o)
        record = {
            "schema": self.schemas[-1] if self.schemas else None,
            "schema_path": list(self.schemas),
            "object_class": cls,
            "object_type": object_type,
            "field": op.name,
            "operation": f"{type(op).__module__}.{type(op).__qualname__}",
            "operation_path": list(self.operations),
            "source_streams": list(self.source_streams(ar)),
            "length_rule": rule,
            "declared_length": declared,
            "observed_length": 0,
            "completed": False,
        }
        self.raw_operations.append(record)
        return record

    def snapshot(self):
        calls = [{
            "schema": name,
            "via": via,
            "parent_schema": parent,
            "object_class": cls,
            "object_type": object_type,
            "source_streams": list(streams),
            "count": count,
        } for (name, via, parent, cls, object_type, streams), count in self.calls.items()]
        calls.sort(key=lambda item: (item["schema"], item["via"], item["parent_schema"] or "", item["object_class"] or "", item["object_type"], item["source_streams"]))
        return {
            "direction": self.direction,
            "requested_stream": self.stream,
            "role": self.role,
            "completed": self.completed,
            "used_schemas": sorted(self.used),
            "provisional_schemas": sorted(self.used & self.registry.tentative),
            "missing_schemas": sorted(self.missing),
            "schema_calls": calls,
            "raw_operations": list(self.raw_operations),
        }


class Op:
    pass


class P(Op):
    def __init__(self, kind, name):
        self.kind, self.name = kind, name

    def load(self, ar, scope, o):
        scope[self.name] = ar.prim(self.kind)

    def store(self, ar, scope, o):
        ar.prim(self.kind, scope[self.name])


class S(Op):
    def __init__(self, name):
        self.name = name

    def load(self, ar, scope, o):
        scope[self.name] = ar.string()

    def store(self, ar, scope, o):
        ar.string(scope[self.name])


class O(Op):
    def __init__(self, name):
        self.name = name

    def load(self, ar, scope, o):
        scope[self.name] = ar.obj()

    def store(self, ar, scope, o):
        ar.obj(scope[self.name])


class C(Op):
    def __init__(self, name):
        self.name = name

    def load(self, ar, scope, o):
        scope[self.name] = ar.cls()

    def store(self, ar, scope, o):
        ar.cls(scope[self.name])


class Cnt(Op):
    def __init__(self, name):
        self.name = name

    def load(self, ar, scope, o):
        scope[self.name] = ar.count_value()

    def store(self, ar, scope, o):
        ar.count_value(scope[self.name])


class Raw(Op):
    def __init__(self, name, n):
        self.name, self.n = name, n

    def load(self, ar, scope, o):
        n = self.n(scope, ar) if callable(self.n) else self.n
        usage = getattr(ar.registry, "_usage", None)
        record = usage.raw(self, ar, o, n) if usage is not None else None
        start = ar.p
        try:
            scope[self.name] = ar.raw(n)
            if record is not None:
                record["completed"] = True
        finally:
            if record is not None:
                record["observed_length"] = ar.p - start

    def store(self, ar, scope, o):
        n = self.n(scope, ar) if callable(self.n) else self.n
        usage = getattr(ar.registry, "_usage", None)
        record = usage.raw(self, ar, o, n) if usage is not None else None
        start = len(ar.out)
        try:
            data = scope[self.name]
            if len(data) != n:
                raise ArchiveError(f"{self.name} declares {n} bytes, got {len(data)}")
            ar.raw(data)
            if record is not None:
                record["completed"] = True
        finally:
            if record is not None:
                record["observed_length"] = len(ar.out) - start


class Base(Op):
    def __init__(self, cls):
        self.cls = cls

    def load(self, ar, scope, o):
        ar.registry.run_load(self.cls, ar, scope, o, via="base")

    def store(self, ar, scope, o):
        ar.registry.run_store(self.cls, ar, scope, o, via="base")


class Emb(Op):
    def __init__(self, name, cls):
        self.name, self.cls = name, cls

    def load(self, ar, scope, o):
        sub = Scope(scope, None)
        ar.registry.run_load(self.cls, ar, sub, o, via="embedded")
        scope[self.name] = sub.own

    def store(self, ar, scope, o):
        ar.registry.run_store(self.cls, ar, Scope(scope, None, scope[self.name]), o, via="embedded")


class If(Op):
    def __init__(self, pred, then, other=()):
        self.pred, self.then, self.other = pred, list(then), list(other)

    def load(self, ar, scope, o):
        body = self.then if self.pred(scope, ar) else self.other
        run_load(body, ar, scope, o)

    def store(self, ar, scope, o):
        body = self.then if self.pred(scope, ar) else self.other
        run_store(body, ar, scope, o)


class Rep(Op):
    def __init__(self, count, name, body):
        self.count, self.name, self.body = count, name, list(body)

    def load(self, ar, scope, o):
        n = self.count(scope, ar) if callable(self.count) else scope[self.count]
        if n < 0 or n > 10_000_000:
            raise ArchiveError(f"implausible repeat {n} for {self.name}")
        items = []
        for i in range(n):
            sub = Scope(scope, i)
            run_load(self.body, ar, sub, o)
            items.append(sub.own)
        scope[self.name] = items

    def store(self, ar, scope, o):
        n = self.count(scope, ar) if callable(self.count) else scope[self.count]
        if len(scope[self.name]) != n:
            raise ArchiveError(f"{self.name} declares {n} items, got {len(scope[self.name])}")
        for i, item in enumerate(scope[self.name]):
            sub = Scope(scope, i, item)
            run_store(self.body, ar, sub, o)


class Until(Op):
    def __init__(self, stop, name, body):
        self.stop, self.name, self.body = stop, name, list(body)

    def load(self, ar, scope, o):
        items = []
        while True:
            sub = Scope(scope, len(items))
            run_load(self.body, ar, sub, o)
            items.append(sub.own)
            if self.stop(sub, ar):
                break
        scope[self.name] = items

    def store(self, ar, scope, o):
        for i, item in enumerate(scope[self.name]):
            run_store(self.body, ar, Scope(scope, i, item), o)


class Fn(Op):
    def __init__(self, load, store):
        self.fload, self.fstore = load, store

    def load(self, ar, scope, o):
        self.fload(ar, scope, o)

    def store(self, ar, scope, o):
        self.fstore(ar, scope, o)


class Scope:
    def __init__(self, parent, index, own=None):
        self.parent = parent
        self.index = index
        self.own = {} if own is None else own

    def __getitem__(self, k):
        if k in self.own:
            return self.own[k]
        return self.parent[k]

    def __setitem__(self, k, v):
        self.own[k] = v

    def __contains__(self, k):
        return k in self.own or k in self.parent

    def get(self, k, d=None):
        try:
            return self[k]
        except KeyError:
            return d


def run_load(ops, ar, scope, o):
    for index, op in enumerate(ops):
        usage = getattr(ar.registry, "_usage", None)
        if usage is None:
            op.load(ar, scope, o)
        else:
            with usage.operation(op, index, scope):
                try:
                    op.load(ar, scope, o)
                except ArchiveError as error:
                    if not hasattr(error, "details"):
                        fields = getattr(scope, "own", scope)
                        error.details = {
                            "schema_path": list(usage.schemas),
                            "operation_path": list(usage.operations),
                            "object_class": o.cls if isinstance(o, Obj) else None,
                            "cursor": ar.p, "remaining": ar.left(),
                            "fields": {key: value for key, value in fields.items() if isinstance(value, (int, float))},
                            "counts": {key: len(value) for key, value in fields.items() if isinstance(value, list)},
                        }
                    raise


def run_store(ops, ar, scope, o):
    for index, op in enumerate(ops):
        usage = getattr(ar.registry, "_usage", None)
        if usage is None:
            op.store(ar, scope, o)
        else:
            with usage.operation(op, index, scope):
                op.store(ar, scope, o)


class Registry:
    def __init__(self):
        self.classes = {}
        self.tentative = set()
        self.plans = {}
        self._usage = None

    @contextmanager
    def track_usage(self, direction, stream, *, role="stream", sources=None):
        if direction not in ("load", "store"):
            raise ValueError(f"unknown usage direction {direction!r}")
        previous = self._usage
        usage = Usage(self, direction, stream, role, sources)
        self._usage = usage
        try:
            yield usage
            usage.completed = True
        finally:
            self._usage = previous

    @contextmanager
    def schema_usage(self, name, ar, o, via):
        if self._usage is None:
            yield
        else:
            with self._usage.schema(name, ar, o, via):
                yield

    def define(self, name, ops):
        if name in self.classes and name not in self.tentative:
            raise ValueError(f"duplicate class {name}")
        self.tentative.discard(name)
        self.classes[name] = list(ops)

    def provisional(self, name, ops):
        if name in self.classes:
            return
        self.tentative.add(name)
        self.classes[name] = list(ops)

    def has(self, name):
        return name in self.classes

    def run_load(self, name, ar, scope, o, *, via="direct"):
        with self.schema_usage(name, ar, o, via):
            if name not in self.classes:
                raise ArchiveError(f"no schema for {name} at {ar.p}")
            run_load(self.classes[name], ar, scope, o)

    def run_store(self, name, ar, scope, o, *, via="direct"):
        with self.schema_usage(name, ar, o, via):
            if name not in self.classes:
                raise ArchiveError(f"no schema for {name} at {len(ar.out)}")
            try:
                run_store(self.classes[name], ar, scope, o)
            except KeyError as error:
                raise ArchiveError(f"missing field {error.args[0]!r} in {name} while storing {o.cls} at {len(ar.out)}") from error

    def load(self, ar, o):
        self.run_load(o.cls, ar, o.f, o, via="object")

    def store(self, ar, o):
        self.run_store(o.cls, ar, o.f, o, via="object")
