from __future__ import annotations

from Core import ArchiveError, Load, Store


class StreamDoc:
    def __init__(self, name, head, roots, tail=b""):
        self.name = name
        self.head = head
        self.roots = roots
        self.tail = tail


def load_resolved(data, reg, version=None):
    ar = Load(data, 1, reg, version)
    base = ar.prim("u32")
    ar.count = base
    ar.base = base
    n = ar.count_value()
    roots = [ar.obj() for _ in range(n)]
    rest = ar.raw(ar.left())
    return StreamDoc("resolved", {"base": base, "n": n}, roots, rest), ar


def store_resolved(doc, reg, version=None):
    ar = Store(doc.head["base"], reg, version)
    ar.prim("u32", doc.head["base"])
    ar.count_value(len(doc.roots))
    for o in doc.roots:
        ar.obj(o)
    ar.raw(doc.tail)
    return bytes(ar.out)


def load_rooted(data, reg, base, version=None):
    ar = Load(data, base, reg, version)
    roots = []
    while ar.left() >= 2:
        roots.append(ar.obj())
    rest = ar.raw(ar.left())
    return StreamDoc("rooted", {"base": base}, roots, rest), ar


def store_rooted(doc, reg, version=None):
    ar = Store(doc.head["base"], reg, version)
    for o in doc.roots:
        ar.obj(o)
    ar.raw(doc.tail)
    return bytes(ar.out)
