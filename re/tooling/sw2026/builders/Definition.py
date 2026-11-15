from __future__ import annotations

import math
from collections.abc import Iterable

from Core import ArchiveError, Obj
from Streams import StreamDoc
from defs.Definition import STANDARDS, store_definition

from builders.Model import object_list


def identity_transform() -> dict:
    return {
        "has_matrix": 0,
        "f58": 0.0,
        "f60": 0.0,
        "f68": 0.0,
        "f70": 1.0,
        "f78": 0,
    }


def document_preferences() -> dict:
    return {
        "f08": 0,
        "f0c": 100,
        "f10": 5,
        "f2c": 0,
        "f18": 0,
        "f1c": 1,
        "f20": 0,
        "f24": 0,
        "f28": 0,
        "f14": 1,
        "f30": 0,
        "f34": 0,
    }


def notebook(*, name: str) -> dict:
    if not isinstance(name, str) or not name or "\x00" in name:
        raise ValueError("journal names must be nonempty strings without null characters")
    return {
        "f18": Obj("uoJournal_c", {"f08": name, "f10": 0, "f18": 0}, schema=0),
        "f10": object_list(),
        "f28": 1,
        "f20": object_list(),
        "f38": 1,
        "f30": object_list(),
        "pending": object_list(),
    }


def part_definition(
    *,
    density_kg_m3: float,
    drafting_standard: str,
    detail_flags: Iterable[int],
    tessellation: tuple[int, int, int, bool],
    system_preference_7a: bool,
    journal_name: str,
) -> Obj:
    if isinstance(density_kg_m3, bool) or not isinstance(density_kg_m3, (int, float)):
        raise TypeError("document density must be numeric")
    if not math.isfinite(density_kg_m3) or density_kg_m3 <= 0:
        raise ValueError("document density must be finite and positive")
    if drafting_standard not in STANDARDS:
        raise ArchiveError("unsupported drafting-standard runtime class")
    flags = frozenset(detail_flags)
    if any(type(value) is not int or not 0 <= value < 64 for value in flags):
        raise ValueError("document display flags must be integer bit positions below 64")
    if not isinstance(tessellation, tuple) or len(tessellation) != 4:
        raise TypeError("tessellation must contain three integers and one boolean")
    if any(type(value) is not int or not 0 <= value <= 0x7FFFFFFF for value in tessellation[:3]):
        raise ValueError("tessellation settings must fit nonnegative signed integers")
    if type(tessellation[3]) is not bool or type(system_preference_7a) is not bool:
        raise TypeError("document preference flags must be booleans")
    mask = sum(1 << bit for bit in flags)
    low = mask & 0xFFFFFFFF
    high = mask >> 32
    result = Obj("uiPartDoc_c")
    result.f.update({name: 0 for name in (
        "fac8", "fb54", "f850", "fb00", "fb04", "fa6c", "f1000", "f7b8",
        "f1348", "f1350", "f134c", "f1354", "fa78", "f1358", "f7bc",
        "f13c8", "f13f0", "fa7c", "fa80", "f1424", "f930", "f1304", "f3e8",
    )})
    result.f.update({name: None for name in ("fac0", "fb20", "fab8", "fa10", "f12e8")})
    result.f.update({name: "" for name in ("f1138", "f1150", "f1140")})
    result.f.update({
        "fa58": tessellation[0],
        "fa5c": tessellation[1],
        "fa60": tessellation[2],
        "fa64": int(tessellation[3]),
        "fa74": 1,
        "clsid_a": 0x83A33D30,
        "clsid_b": 0x27C5,
        "clsid_c": 0x11CE,
        "clsid_d": bytes.fromhex("bfd400400513bb57"),
        "fae8": identity_transform(),
        "faf0": identity_transform(),
        "facc": 3,
        "fad0": 0,
        "fad4": 3,
        "fad8_0": low if low < 0x80000000 else low - 0x100000000,
        "fad8_1": high if high < 0x80000000 else high - 0x100000000,
        "fba8": Obj(drafting_standard),
        "f878": {"n": 0, "styles": []},
        "f870": Obj("uiLineFontMgr_c", {"n": 0, "f10": []}),
        "nenv": 0,
        "faf8": [],
        "basedoc": {"ole": {"n": 0, "f7f8": []}, "f2a0": 0},
        "fbf0": {"f08": None, "f10": 0},
        "fb3c": -1,
        "fb40": -1,
        "fd68": 0x12035,
        "fa98": 0x203,
        "ffd8": notebook(name=journal_name),
        "fa90": int(system_preference_7a),
        "f1014": 1,
        "expand_keys": {"n": 0, "items": []},
        "expand_vals": {"n": 0, "items": []},
        "has_pwmaterial": 0,
        "f1158": object_list(),
        "ff40": object_list(),
        "ff88": {"n": 0, "items": []},
        "ffb0": {"n": 0, "items": []},
        "f1370": document_preferences(),
        "f1388": 1,
        "f1390": 1,
        "f135c": 1,
        "f13d0": {"n": 0, "items": []},
        "f1400": 1,
        "f1408": 1,
        "fd78": 2,
        "f1368": 1,
        "fd7c": 3,
        "nvar": 0,
        "f11a0": [],
        "f1688": float(density_kg_m3),
    })
    return result


def definition_stream(*, registry, document: Obj) -> bytes:
    if not isinstance(document, Obj) or document.cls != "uiPartDoc_c":
        raise ArchiveError("definition construction currently requires a part document")
    return store_definition(StreamDoc("definition", document, [document]), registry, 19000)
