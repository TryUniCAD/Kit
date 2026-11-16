from __future__ import annotations

from Core import ArchiveError, Obj
from Dsl import Vge, base, obj, ver
from Schema import Fn, Op, Rep
from defs.ResolvedCore import PARENT, concept_vt

MASTER = "moSheetMetalMaster_c"


def version_2026(ar, scope, owner):
    if ver(ar) != 19000:
        raise ArchiveError("direct sheet metal master ownership requires archive version 19000")


def body_types(ar, scope, owner):
    for row in scope["f358"]:
        value = row["o"]
        if value is not None and (not isinstance(value, Obj) or value.cls != "moPerBodySheetMetalData_c"):
            raise ArchiveError("sheet metal master list requires its proven concrete per-body type")


class DirectMaster(Op):
    name = "f1018"

    def load(self, ar, scope, owner):
        value = Obj(MASTER)
        ar.registry.run_load(MASTER, ar, value.f, value)
        scope[self.name] = value

    def store(self, ar, scope, owner):
        value = scope[self.name]
        if not isinstance(value, Obj) or value.cls != MASTER:
            raise ArchiveError("part bridge data requires the actual typed sheet metal master")
        ar.registry.run_store(MASTER, ar, value.f, value)


def define(reg):
    from defs.ConfigPart import Len, Pos

    PARENT[MASTER] = "moFeature_c"
    concept_vt(MASTER)
    reg.define(MASTER, [
        Fn(version_2026, version_2026),
        base("moFeature_c"),
        Vge(0x1061, [
            Len("i32", "n370", "f358"),
            Rep(Pos("n370"), "f358", [obj("o")]),
            Fn(body_types, body_types),
        ]),
    ])
