from __future__ import annotations

from Core import ArchiveError, Load, Store
from Dsl import cstr, i32, ver
from Schema import Fn, Op, Rep


class MfcCount(Op):
    def __init__(self, name):
        self.name = name

    def load(self, ar, scope, o):
        value = ar.prim("u16")
        if value == 0xFFFF:
            value = ar.prim("u32")
            if value == 0xFFFFFFFF:
                value = ar.prim("u64")
        scope[self.name] = value

    def store(self, ar, scope, o):
        value = scope[self.name]
        if not isinstance(value, int) or not 0 <= value <= 0xFFFFFFFFFFFFFFFF:
            raise ArchiveError(f"MFC count {self.name} is outside the unsigned 64-bit domain")
        if value < 0xFFFF:
            ar.prim("u16", value)
        else:
            ar.prim("u16", 0xFFFF)
            if value < 0xFFFFFFFF:
                ar.prim("u32", value)
            else:
                ar.prim("u32", 0xFFFFFFFF)
                ar.prim("u64", value)


def require_ordinary_mfc_map(ar, scope, o):
    if not isinstance(ar, (Load, Store)):
        raise ArchiveError("MFC map owner requires an ordinary Core archive")
    version = ver(ar)
    if version != 19000:
        raise ArchiveError(f"MFC map owner requires ordinary version 19000, got {version}")


def define(reg):
    reg.define("su_CMapStringToInt", [
        Fn(require_ordinary_mfc_map, require_ordinary_mfc_map),
        MfcCount("n"),
        Rep("n", "items", [cstr("k"), i32("v")]),
    ])
