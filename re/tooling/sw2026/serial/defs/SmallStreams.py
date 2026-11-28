from __future__ import annotations

from Core import Load, Obj, Store
from Dsl import i32, u32, obj, time32
from Streams import StreamDoc


def flat(cls):
    def load(data, reg, version=None, *, archive=None, name=None):
        ar = Load(data, 1, reg, version)
        o = Obj(cls)
        reg.run_load(cls, ar, o.f, o)
        rest = ar.raw(ar.left())
        return StreamDoc(cls, {}, [o], rest), ar

    def store(doc, reg, version=None):
        ar = Store(1, reg, version)
        for o in doc.roots:
            reg.run_store(o.cls, ar, o.f, o)
        ar.raw(doc.tail)
        return bytes(ar.out)

    return ("custom", (load, store))


PLANS = {
    "ModelStamps": flat("ModelStamps.load"),
    "_DL_VERSION_19000/DLUpdateStamp": flat("DLUpdateStamp.load"),
    "Contents/eModelLic": flat("eModelLic.save"),
}


def define(reg):
    reg.define("ModelStamps.load", [time32("creation"), u32("update_stamp"), u32("body_stamp")])
    reg.define("DLUpdateStamp.load", [u32("stamp"), obj("o")])
    reg.define("eModelLic.save", [i32("license_pkg_type")])
