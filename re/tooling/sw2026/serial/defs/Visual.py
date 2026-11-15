from __future__ import annotations

from Core import ArchiveError, Load, Store
from Dsl import Vgt, Vlt, ver, i32, u32, cstr, obj, rep, base
from Schema import If, Fn
import Streams

VIS_CONDITIONS = 0x20004000


def flag(name, default=0):
    return lambda s, ar: ar.ctx.get(name, default) != 0


def legacy(what):
    def fail(ar, scope, o):
        raise ArchiveError(f"legacy branch {what} not modelled at {getattr(ar, 'p', '?')}")
    return Fn(fail, fail)


def Vin(lo, hi, then):
    return If(lambda s, ar: lo < ver(ar) < hi, then)


def attr_map(n, name):
    return [
        u32(n),
        rep(n, name, [
            i32("key"),
            u32("k"),
            rep("k", "objs", [obj("o")]),
        ]),
    ]


def define_attributes(reg):
    reg.define("visStateAttribute_c", [
        Vgt(0xDC9, [u32("f08")]),
    ])
    reg.define("visStateDisplayStateAttribute_c", [
        base("visStateAttribute_c"),
        cstr("f10"),
        Vgt(0xB9F, [i32("f18")]),
    ])
    reg.define("visStateVisualPropertiesAttribute_c", [
        base("visStateAttribute_c"),
        obj("f10"),
    ])
    reg.define("visStateVisualStateAttribute_c", [
        base("visStateAttribute_c"),
        i32("f10"),
        i32("f14"),
        i32("f18"),
        i32("f1c"),
    ])


def define_key_data(reg):
    reg.define("visStateKeyData_c.FUN_32742fd0", [
        Vlt(0x1197, [legacy("visStateKeyData_c header pre-0x1197")]),
        i32("f15c"),
        i32("f158"),
        Vlt(0xD95, [legacy("visStateKeyData_c config list pre-0xd95")]),
        i32("n_ids"),
        rep(lambda s, ar: max(s["n_ids"], 0), "f118", [
            i32("key"),
            i32("value"),
            i32("one"),
        ]),
        i32("n_states"),
        rep(lambda s, ar: max(s["n_states"], 0), "f0f0", [
            i32("id"),
            cstr("name"),
            Vgt(0xE2E, [i32("f384")]),
            Vgt(0x1304, [i32("f394")]),
            Vgt(0x1C0D, [i32("f38c")]),
        ]),
    ])
    reg.provisional("moDisplayedEntityTracker_c.Serialize", [
        i32("n"),
        rep(lambda s, ar: max(s["n"], 0), "f08", [
            cstr("key"),
            obj("ref"),
        ]),
    ])
    reg.define("visStateKeyData_c", [
        base("visStateKeyData_c.FUN_32742fd0"),
        If(flag("vis_skip_body"), [], [
            u32("n_comps"),
            rep("n_comps", "comps", [
                obj("comp"),
                *attr_map("m", "attrs"),
            ]),
            Vin(0xB7F, 0xBA0, [i32("old_b7f")]),
            Vgt(0xF33, [
                u32("n_ents"),
                rep("n_ents", "f78", [
                    obj("ref"),
                    *attr_map("m", "attrs"),
                ]),
            ]),
            Vgt(0xF4F, [*attr_map("n_f88", "f88")]),
            Vgt(0x1100, [base("moDisplayedEntityTracker_c.Serialize")]),
            If(flag("vis_wrapped"), [
                i32("n148_hi"),
                i32("n148_lo"),
                rep(lambda s, ar: (s["n148_hi"] << 32) | (s["n148_lo"] & 0xFFFFFFFF), "f148", [
                    i32("key"),
                    i32("value"),
                ]),
            ]),
        ]),
    ])


def load_visual_states(data, reg, version=None, *, archive=None, name=None):
    ar = Load(data, 1, reg, version, {"conditions": VIS_CONDITIONS})
    file_version = ar.prim("u32")
    ar.version = file_version
    shown = ar.prim("i32")
    root = ar.obj()
    rest = ar.raw(ar.left())
    head = {"file_version": file_version, "shown": shown, "root": root}
    return Streams.StreamDoc("visual_states", head, [root], rest), ar


def store_visual_states(sd, reg, version=None):
    ar = Store(1, reg, sd.head["file_version"], {"conditions": VIS_CONDITIONS})
    ar.prim("u32", sd.head["file_version"])
    ar.prim("i32", sd.head["shown"])
    ar.obj(sd.head["root"])
    ar.raw(sd.tail)
    return bytes(ar.out)


PLANS = {
    "ThirdPtyStore/VisualStates": ("custom", (load_visual_states, store_visual_states)),
}


def define(reg):
    define_attributes(reg)
    define_key_data(reg)
    reg.provisional("moCompHolder_c", [base("moCompRef_c")])
