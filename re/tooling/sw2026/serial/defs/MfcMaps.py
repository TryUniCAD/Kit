from __future__ import annotations

from Core import ArchiveError, Load, Store
from Dsl import cstr, i32, ver
from Schema import Fn, Op, Rep


class MfcCount(Op):
    def __init__(self, name):
        self.name = name

    def load(self, ar, scope, o):
        scope[self.name] = ar.count_value(framework=True)

    def store(self, ar, scope, o):
        ar.count_value(scope[self.name], framework=True)


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
