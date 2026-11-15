from __future__ import annotations

from Core import ArchiveError


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
        scope[self.name] = ar.raw(n)

    def store(self, ar, scope, o):
        n = self.n(scope, ar) if callable(self.n) else self.n
        data = scope[self.name]
        if len(data) != n:
            raise ArchiveError(f"{self.name} declares {n} bytes, got {len(data)}")
        ar.raw(data)


class Base(Op):
    def __init__(self, cls):
        self.cls = cls

    def load(self, ar, scope, o):
        ar.registry.run_load(self.cls, ar, scope, o)

    def store(self, ar, scope, o):
        ar.registry.run_store(self.cls, ar, scope, o)


class Emb(Op):
    def __init__(self, name, cls):
        self.name, self.cls = name, cls

    def load(self, ar, scope, o):
        sub = Scope(scope, None)
        ar.registry.run_load(self.cls, ar, sub, o)
        scope[self.name] = sub.own

    def store(self, ar, scope, o):
        ar.registry.run_store(self.cls, ar, Scope(scope, None, scope[self.name]), o)


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
    for op in ops:
        op.load(ar, scope, o)


def run_store(ops, ar, scope, o):
    for op in ops:
        op.store(ar, scope, o)


class Registry:
    def __init__(self):
        self.classes = {}
        self.tentative = set()
        self.plans = {}

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

    def run_load(self, name, ar, scope, o):
        if name not in self.classes:
            raise ArchiveError(f"no schema for {name} at {ar.p}")
        run_load(self.classes[name], ar, scope, o)

    def run_store(self, name, ar, scope, o):
        if name not in self.classes:
            raise ArchiveError(f"no schema for {name} at {len(ar.out)}")
        try:
            run_store(self.classes[name], ar, scope, o)
        except KeyError as error:
            raise ArchiveError(f"missing field {error.args[0]!r} in {name} while storing {o.cls} at {len(ar.out)}") from error

    def load(self, ar, o):
        self.run_load(o.cls, ar, o.f, o)

    def store(self, ar, o):
        self.run_store(o.cls, ar, o.f, o)
