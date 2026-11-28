from __future__ import annotations

from Core import Obj


def material_properties() -> dict:
    return {
        "f28": "", "f20": "", "f30": "", "fb8": "",
        "f38": 1.0, "f40": 1.0, "f48": 1.0, "f50": 0.3125,
        "f58": 0.0, "f60": 0.0,
        "f68": 1, "f6c": 0, "f70": 1, "f74": 1, "f78": 1, "f7c": 1,
        "has80": 0, "has90": 0, "has98": 0,
        "props": {"n": 0, "props": []},
    }


def visual_properties() -> Obj:
    return Obj("moVisualProperties_c", {
        "f0c": 0xC0C0C0, "f14": 0, "f18": 0xC0C0C0,
        "f20": material_properties(),
        "f40": "", "f48": 0, "f4c": 1, "f50": "",
        "f58": 0, "f5c": 0, "f78": -1, "f7c": 0, "f80": 0,
        "has88": 0,
    })


def model_visual_properties() -> Obj:
    result = visual_properties()
    result.f["f5c"] = 1
    return result
