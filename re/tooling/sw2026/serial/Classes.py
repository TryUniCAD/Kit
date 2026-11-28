from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

from Schema import Registry, Cnt, O, Rep, S, P, Raw

PACKAGES = ("defs",)


def containers(reg):
    reg.define("suObList", [Cnt("n"), Rep("n", "items", [O("o")])])
    reg.define("su_CObList", [Cnt("n"), Rep("n", "items", [O("o")])])
    reg.define("su_CObArray", [Cnt("n"), Rep("n", "items", [O("o")])])
    reg.define("su_CStringArray", [Cnt("n"), Rep("n", "items", [S("s")])])
    reg.define("su_CDWordArray", [Cnt("n"), Rep("n", "items", [P("u32", "v")])])
    reg.define("su_CWordArray", [Cnt("n"), Rep("n", "items", [P("u16", "v")])])
    reg.define("su_CByteArray", [Cnt("n"), Raw("data", lambda s, ar: s["n"])])


def registry():
    reg = Registry()
    containers(reg)
    here = Path(__file__).resolve().parent
    for pkg in PACKAGES:
        d = here / pkg
        if not d.exists():
            continue
        for info in sorted(pkgutil.iter_modules([str(d)]), key=lambda m: m.name):
            mod = importlib.import_module(f"{pkg}.{info.name}")
            mod.define(reg)
            for k, v in getattr(mod, "PLANS", {}).items():
                if k in reg.plans:
                    raise ValueError(f"duplicate plan {k}")
                reg.plans[k] = v
    return reg
