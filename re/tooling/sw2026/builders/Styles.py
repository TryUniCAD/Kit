from __future__ import annotations

import math
from collections.abc import Sequence

from builders.Units import unit_record


def number(value, name, low=None):
    try:
        valid = type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError(f"{name} must be a finite authored number")
    value = float(value)
    if low is not None and value < low:
        raise ValueError(f"{name} must be at least {low}")
    return value


def text(value, name):
    if not isinstance(value, str) or "\x00" in value:
        raise ValueError(f"{name} must be authored text without a NUL character")
    return value


def character_format(*, font_name, height_m, point_height, weight=400, line_spacing_m=0.0):
    font_name = text(font_name, "font name")
    if not font_name:
        raise ValueError("an explicit authored font is required; the localized font resource is not a default input")
    if type(point_height) is not int or not 0 <= point_height <= 0x7FFFFFFF:
        raise ValueError("point height must be a nonnegative authored integer")
    if type(weight) is not int or not 1 <= weight <= 1000:
        raise ValueError("font weight must be an authored integer in 1..1000")
    height_m = number(height_m, "character height")
    if height_m <= 0 and height_m != -1 or height_m > 0 and point_height:
        raise ValueError("character height must be positive with point height zero, or use the native -1 point-height mode")
    return {
        "f08": font_name,
        "f10": height_m,
        "f18": point_height,
        "f20": 0.0,
        "f28": number(line_spacing_m, "line spacing", low=0),
        "f30": 0,
        "f38": 1.0,
        "f40": 0.0,
        "f48": 0.0,
        "f50": 1.0,
        "f58": weight,
    }


def line_width(*, category, width_m):
    if type(category) is not int or not 0 <= category <= 7:
        raise ValueError("line-weight category must be a native category in 0..7")
    width_m = number(width_m, "line width")
    if width_m < 0 and width_m != -1:
        raise ValueError("line width must be nonnegative or the native -1 category-width sentinel")
    return {"f06": category, "f00": width_m}


def print_widths(*, widths_m):
    if not isinstance(widths_m, Sequence) or isinstance(widths_m, (str, bytes, bytearray)) or len(widths_m) != 8:
        raise ValueError("the eight authored print line widths are required")
    return {f"f{8 + 4 * index:x}": number(value, "print line width", low=0) for index, value in enumerate(widths_m)}


def string_array(*, values):
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
        raise ValueError("authored names must be a sequence")
    return {"n": len(values), "items": [{"s": text(value, "authored name")} for value in values]}


def line_font(*, name):
    return {"f08": text(name, "line-style name"), "f10": line_width(category=0, width_m=-1), "f18": 0}


def helper_format(*, font_name):
    return character_format(font_name=font_name, height_m=-1, point_height=0, line_spacing_m=0.001)


def annotation_data(*, font_name):
    return {
        "f08": helper_format(font_name=font_name),
        "f68": 3, "f6c": -1, "f70": 0, "f74": 0, "f78": 1,
        "f7c": 1, "f80": 0, "f88": 0.0, "f90": 0,
        "f94": 1, "f98": 0, "fa0": 0.0, "fa8": 0,
    }


def dimension_style(*, kind, font_name, line_style_name):
    allowed = {"base", "linear", "angle", "arc_length", "radial", "hole", "ordinate", "angular_ordinate", "chamfer", "diameter"}
    if kind not in allowed:
        raise ValueError(f"unsupported dimension style {kind!r}")
    f = {
        "f08": 1, "fc": 1, "f10": 1, "f18": 1.0, "f20": 0.0127,
        "f28": 1, "f30": 1.0, "f38": 0.0127, "f40": 1, "f44": 0,
        "f48": "", "f50": "", "f58": 0.0, "f60": 0.0,
        "f68": 1, "f6c": 0, "f70": 1, "f74": 0, "f78": 0,
        "f80": 2, "f84": 3, "f88": 2, "f8c": 3, "f90": -1,
        "f94": 0, "f98": 0, "f9c": 0, "fc0": 1, "fe0": 0xC0,
        "fd0": line_font(name=line_style_name), "fd8": line_font(name=line_style_name),
        "fe8": character_format(font_name=font_name, height_m=0.0035, point_height=0),
        "ff0": unit_record(kind="length", unit_code=2, decimal_places=2).f,
        "ff8": unit_record(kind="angle", unit_code=0, decimal_places=2).f,
    }
    if kind == "linear":
        f.update({"f100": 2, "f104": 0, "f108": 0})
    elif kind == "angle":
        f["f100"] = 0x142
    elif kind == "radial":
        f.update({"f100": 2, "f104": 1})
    elif kind == "hole":
        f.update({"f100": 0, "f94": 1})
    elif kind == "ordinate":
        f.update({"f100": 1, "f104": 1, "f108": 0.0015875})
    elif kind == "angular_ordinate":
        f.update({"f100": 1, "f104": 0x15, "f108": 0, "f110": 0, "f114": 0, "f84": 2, "f8c": 2})
    elif kind == "chamfer":
        f.update({"f100": 0, "f104": 1, "f108": 2, "f10c": 2, "f110": 0,
                  "f118": 0.0, "f120": 0.0, "f128": 0, "f6c": 3, "f10": 2, "f94": 1})
    elif kind == "diameter":
        f.update({"f100": 1, "f104": 0})
    return f


def dimension_definitions(*, font_name, line_style_name):
    f = {
        "f8": 0.001016, "f10": 0.003302, "f18": 0.00635, "f20": 0.001,
        "f28": 0.001, "f30": 0.005, "f38": 0.01, "f40": 0.003175,
        "f48": 0.001524, "f50": 0.00635, "f58": -25.0,
        "f60": 0, "f64": 0, "f68": 1, "f6c": 1, "f70": 20, "f74": 0,
        "f78": 0.0, "f80": 0.0, "f88": 0, "f8c": 0,
        "f90": 0.01, "f98": 0.006, "fa0": 0.26179938779915,
        "fa8": 1, "fb0": 1.0, "fb8": 0, "fbc": 1, "fc0": 1, "fc4": 1,
        "fcc": 1, "fd0": 1, "fd4": 1, "fd8": 0x20B1,
    }
    for field, kind in (("fe0", "linear"), ("f1f0", "angle"), ("f2f8", "arc_length"),
                        ("f3f8", "radial"), ("f500", "hole"), ("f608", "ordinate"),
                        ("f718", "angular_ordinate"), ("f830", "chamfer"),
                        ("f960", "diameter"), ("fa68", "base")):
        f[field] = dimension_style(kind=kind, font_name=font_name, line_style_name=line_style_name)
    return f


def surface_finish_data(*, font_name):
    f = {"f08": 0, "f78": 0, "f7c": 0, "f80": 0.78539816339745, "f98": 0, "f9c": 0, "fb0": 0.0, "fb8": 1,
         "fc0": helper_format(font_name=font_name), "f128": annotation_data(font_name=font_name)}
    f.update({f"f{offset:x}": "" for offset in (0x10, 0x18, 0x20, 0x28, 0x30, 0x38, 0x40, 0x48, 0x50, 0x58, 0x88, 0x90)})
    f.update({f"f{offset:x}": 0 for offset in (0x68, 0x6C, 0x70, 0x74, 0xA0, 0xA4, 0xA8, 0xAC, 0x120, 0x124)})
    return f


def note_data(*, font_name):
    f = {
        "f8": "", "f10": 1, "f18": "", "f20": "", "f28": "",
        "f30": 1, "f34": 0, "f38": 0, "f3c": 0, "f40": 0, "f44": 0,
        "f48": 0, "f4c": 1, "f50": 0.0, "f58": 1, "f5c": 0, "f60": 2,
        "f68": 0.01016, "f70": 0.0, "f78": 0, "f7c": 0, "f80": 0, "f84": 3,
        "f88": 10, "f8c": 0, "f90": 1e-6, "f98": 1e-6,
        "fa0": 1, "fa4": 1, "fa8": 0, "fac": 1, "fb0": 1, "fb4": 1,
        "fb8": 1, "fbc": 1, "fc0": 1, "fc8": helper_format(font_name=font_name),
        "f128": 0, "f12c": 0, "f130": 0, "f134": 1, "f138": 0,
        "f13c": 0, "f140": 0, "f144": 0, "f148": 0, "f14c": 0,
        "f150": annotation_data(font_name=font_name), "f218": 0, "f21c": 1,
        "f220": "X", "f228": 0.001, "f230": 1, "f234": 1, "f238": 0,
        "f23c": 0, "f240": 0, "f244": 0, "n248": 0, "f248": [],
    }
    return f


def weld_data(*, font_name):
    f = {"f08": 0, "f90": "", "fa8": "", "fd8": 0, "fdc": 0, "fe8": 1,
         "ff0": helper_format(font_name=font_name), "f150": 1, "f154": 1,
         "f158": helper_format(font_name=font_name), "f1b8": helper_format(font_name=font_name),
         "f260": surface_finish_data(font_name=font_name), "f268": surface_finish_data(font_name=font_name)}
    f.update({f"f{0x10 + 8 * side + 0x10 * index:x}": "" for side in range(2) for index in range(8)})
    f.update({f"f{0x218 + 8 * index:x}": "" for index in range(5)})
    f.update({f"f{offset:x}": 0 for offset in (0x98, 0x9C, 0xA0, 0xA4, 0xB0, 0xB4, 0xB8, 0xBC, 0xC0, 0xC4, 0xC8, 0xCC, 0xD0, 0xD4, 0xE0, 0xE4, 0x240, 0x244, 0x248, 0x24C, 0x250, 0x254, 0x258)})
    return f


def gtol_frame():
    f = {"f08": "", "f10": None, "f18": None, "f20": 0, "f24": 0,
         "f28": 0, "f30": "", "f38": "", "f40": 0, "f48": "", "f50": "",
         "f148": 0, "n2b8": 0, "f2b8": []}
    f.update({f"f{offset:x}": string_array(values=()) for offset in (0x58, 0x80, 0xA8, 0xD0, 0xF8, 0x120)})
    return f


def gtol_data(*, font_name):
    return {
        "n08": 2, "f08": [{"e": gtol_frame()}, {"e": gtol_frame()}],
        "f30": 1, "f34": 2, "f38": "", "f40": 0, "f44": 0, "f48": 0,
        "f4c": 1, "f50": 1, "f54": 0, "f58": 0, "f60": "", "f68": 0,
        "f70": "", "f78": "", "f80": 0, "f88": "", "f90": "", "f98": 0,
        "f9c": 0, "fa0": 0, "fa4": 0, "fa8": 0, "fac": 1,
        "fb0": helper_format(font_name=font_name), "f110": 0, "f114": 0,
        "f118": annotation_data(font_name=font_name), "f1e0": 0,
    }


def center_mark_data(*, font_name):
    return {
        "f08": 0, "f10": 0.0, "f18": 1, "f20": 0.0, "f28": 0, "f2c": 0,
        "f30": 0, "f34": 0, "f38": 0, "f3c": 0, "f40": 1, "f44": 1,
        "f48": 1, "f4c": 0, "f78": 0.0, "f80": annotation_data(font_name=font_name), "f148": 0,
    }


def datum_feature_data(*, font_name):
    return {"f8": 0, "fc": 0, "f10": 0, "f18": "", "f20": 0, "f24": 0,
            "f28": "", "f30": 0, "f34": 0, "f38": 0, "f40": annotation_data(font_name=font_name)}


def datum_target_data(*, font_name):
    return {
        "f08": "", "f10": "", "f18": "", "f20": "", "f28": "",
        "f30": 0, "f34": 0, "f38": 0, "f3c": 1, "f40": 0, "f44": 0,
        "f48": 0, "f4c": 1, "f50": 0.03, "f58": 0.03, "f60": 0,
        "f68": 0.0, "f70": -1, "f74": 0,
        "f78": {"x": 0.0, "y": 0.0, "z": 0.0}, "f90": 0, "fb0": 0,
        "fc0": annotation_data(font_name=font_name),
    }


def annotation_style(*, kind, font_name, language_id):
    if type(language_id) is not int or not 0 <= language_id <= 0xFFFF:
        raise ValueError("language id must be an authored Windows language id")
    f = {
        "f8": 1, "f10": 0.00625, "f18": 1,
        "f1c": 2 if language_id & 0x3FF == 0xD else 0,
        "f20": 0, "f24": 0, "f28": 0, "f34": 0, "f40": 0, "f44": -1,
        "f2c": line_width(category=0, width_m=-1),
        "f38": line_width(category=0, width_m=-1),
        "f50": character_format(font_name=font_name, height_m=0.0035, point_height=0),
    }
    if kind == "base":
        pass
    elif kind == "cloud":
        f["f58"] = 0.00508
    elif kind == "weld":
        f.update({"f58": 0, "f60": character_format(font_name=font_name, height_m=0.00212, point_height=0)})
    elif kind == "surface_finish":
        f.update({"f58": 0, "f5c": 2, "f60": 1.0, "f68": 1.0})
    elif kind == "bend":
        f.update({"f58": 0, "f5c": 0, "f60": 0, "f68": 0.01016})
    elif kind == "gtol":
        f.update({"f58": 1, "f5c": 1, "f60": 0x2E})
    elif kind == "datum":
        f.update({"f58": 0, "f5c": 0, "f60": 1, "f64": 0, "f68": 1, "f6c": 0})
    elif kind == "balloon":
        f.update({"f58": 2, "f5c": 2, "f60": 1, "f64": 1, "f68": 1, "f6c": 2,
                  "f70": "", "f78": "", "f80": 1, "f88": 0.01016, "f90": 0.01016,
                  "f98": 0.0, "fa0": 0.0, "fa8": 0.001, "fb0": 0, "fb4": 0, "fb8": 1, "fc0": "X"})
    elif kind == "view_location":
        f.update({"f58": 7, "f5c": 9, "f60": 11, "f64": 2, "f68": 0.01016,
                  "f70": 1, "f74": 0, "f78": 0.0})
    elif kind == "note":
        f.update({"f58": 0, "f5c": 10, "f60": 0, "f68": 0.01016,
                  "f70": 0.0, "f78": 0.001, "f80": 1})
    else:
        raise ValueError(f"unsupported annotation style {kind!r}")
    return f


def annotation_definitions(*, font_name, language_id):
    f = {"f08": 0.00625, "f10": 1, "f14": 0, "f18": 0, "f1c": 1, "f20": 3,
         "f24": 1, "f28": 0, "f2c": 1, "f30": 1, "f34": 1, "f38": 0}
    for field, kind in (("f40", "cloud"), ("fa0", "weld"), ("f108", "surface_finish"),
                        ("f178", "bend"), ("f1e8", "gtol"), ("f250", "datum"),
                        ("f2c0", "balloon"), ("f398", "view_location"),
                        ("f418", "note"), ("f4a0", "base")):
        f[field] = annotation_style(kind=kind, font_name=font_name, language_id=language_id)
    return f


def table_style(*, kind, font_name):
    f = {"f08": 0, "f0c": -1, "f28": 0, "f2c": 1, "f38": 0,
         "f18": line_width(category=0, width_m=-1),
         "f20": line_width(category=0, width_m=-1),
         "f10": character_format(font_name=font_name, height_m=0.0035, point_height=0)}
    if kind in ("general", "title_block"):
        pass
    elif kind == "revision":
        f.update({"f40": 0, "f44": 0, "f48": 1, "f4c": 0, "f50": "", "f58": 0})
    elif kind == "bom":
        f.update({"f40": 0, "f48": "", "f50": "", "f58": ""})
    elif kind == "hole":
        f.update({"f40": 0, "f44": 0, "f48": 0.008, "f50": 0.78539816339745,
                  "f58": 0, "f5c": 0, "f60": 2, "f64": 2, "f68": 1, "f6c": 1,
                  "f70": 1, "f74": 0, "f78": 0, "f7c": 0})
    elif kind in ("weld", "family"):
        f["f40"] = 0
    elif kind == "bend":
        f.update({"f40": 2, "f44": 2, "f48": 2, "f4c": 0})
    elif kind == "punch":
        f.update({"f40": 0, "f44": 0, "f48": 0, "f4c": 0, "f50": 0,
                  "f58": 0.008, "f60": 0.78539816339745, "f68": 1, "f6c": 2, "f70": 2})
    else:
        raise ValueError(f"unsupported table style {kind!r}")
    return f


def table_definitions(*, font_name):
    f = {"f08": 1, "f328": character_format(font_name=font_name, height_m=0.0035, point_height=0),
         "f330": 0.0005, "f338": 0.001}
    for field, kind in (("f10", "general"), ("f50", "revision"), ("fb0", "bom"),
                        ("f110", "title_block"), ("f150", "hole"), ("f1d0", "weld"),
                        ("f218", "bend"), ("f268", "punch"), ("f2e0", "family")):
        f[field] = table_style(kind=kind, font_name=font_name)
    return f


def swift_options():
    f = {"f10": 0, "fc": -1, "f20": 0, "f90": 0, "f414": 5, "f418": 0,
         "f3dc": 1, "f3e0": 0, "f3e4": 0, "f3e8": 0, "f3ec": 0,
         "f3f0": 1, "f3f4": 1, "f3f8": 1, "f3fc": 0, "f400": 0,
         "f404": 0, "f408": 0, "f40c": 0, "f410": 0,
         "f2b0": 1.0, "f2b8": 0.01, "f2dc": 1}
    for value, offsets in (
        (0.00005, (0x28,)),
        (0.0001, (0x38, 0x48, 0xD8)),
        (0.0002, (0x58, 0x68, 0x190)),
        (-0.0002, (0x1A0,)),
        (0.00025, (0xE8, 0xF8, 0x110, 0x150, 0x2C0)),
        (-0.00025, (0x120, 0x160, 0x2D0)),
        (0.0005, (0xB8, 0xC8, 0x98, 0x130, 0x170, 0x1B0, 0x1D0, 0x2E8, 0x310, 0x338, 0x360)),
        (-0.0005, (0xA8, 0x140, 0x180, 0x1C0, 0x1E0, 0x2F8, 0x320, 0x348, 0x370)),
        (0.00872664625997, (0x290, 0x1F0)),
        (-0.00872664625997, (0x2A0, 0x200)),
        (0.01745329251994, (0x250, 0x270)),
        (-0.01745329251994, (0x260, 0x280)),
    ):
        f.update({f"f{offset:x}": value for offset in offsets})
    for value, offsets in (
        (0, (0x20C, 0x214, 0x224, 0x22C, 0x234, 0x38C, 0x384, 0x104, 0x21C, 0x394)),
        (1, (0x304, 0x32C, 0x354, 0x37C, 0x23C, 0x244, 0x3BC, 0x3C0, 0x39C, 0x3A0,
             0x3A4, 0x3A8, 0x3AC, 0x3B0, 0x3B4, 0x3B8, 0x3C4, 0x3C8, 0x3CC, 0x3D0, 0x3D4, 0x3D8)),
        (2, (0x30, 0x40, 0x50, 0x60, 0x70, 0xC0, 0xF0, 0xD0, 0x100, 0xE0,
             0x118, 0x128, 0x210, 0xA0, 0xB0, 0x108, 0x138, 0x148, 0x218,
             0x158, 0x168, 0x220, 0x198, 0x1A8, 0x230, 0x1B8, 0x1C8,
             0x238, 0x178, 0x188, 0x228, 0x2C8, 0x2D8, 0x2E0, 0x2F0,
             0x300, 0x308, 0x318, 0x328, 0x330, 0x340, 0x350, 0x358,
             0x368, 0x378, 0x380, 0x1D8, 0x1E8, 0x1F8, 0x208, 0x258,
             0x268, 0x278, 0x288, 0x298, 0x2A8, 0x390, 0x398, 0x388, 0x240, 0x248)),
    ):
        f.update({f"f{offset:x}": value for offset in offsets})
    return f


def label_style(*, kind, font_name):
    if kind not in ("detail", "section", "auxiliary", "orthographic", "miscellaneous"):
        raise ValueError(f"unsupported label style {kind!r}")
    f = {"f8": 2, "fc": 1, "f10": 0, "f14": 1, "f18": 1, "f1c": 1,
         "f20": 0, "f24": 0, "f28": 0, "f2c": 0, "f38": 0, "f44": 1,
         "f48": -1, "f58": 0, "f5c": 4, "f88": "", "f90": "",
         "f30": line_width(category=0, width_m=-1),
         "f3c": line_width(category=0, width_m=-1)}
    for offset in (0x98, 0xA0, 0xA8, 0xB0, 0xB8, 0xC0):
        f[f"f{offset:x}"] = character_format(font_name=font_name, height_m=0.0035, point_height=0)
    if kind == "detail":
        f.update({"fc8": 0, "fcc": 0x18})
    elif kind == "section":
        f.update({"fc": 2, "f10": 0, "f2c": 3,
                  "f30": line_width(category=2, width_m=-1),
                  "fc8": 0.00635, "fd0": 0.002032, "fd8": 0.0127,
                  "fe0": 0, "fe4": 2, "fe8": 1, "fec": 1, "ff0": 1})
    elif kind == "auxiliary":
        f.update({"f8": 1, "fc": 1, "f10": 1, "f58": 0, "fc8": 1})
    else:
        f.update({"f8": 0, "fc": 0, "fc8": 0, "fcc": 0})
    return f


def label_definitions(*, font_name):
    f = {"f8": 1, "fc": 1,
         "f458": character_format(font_name=font_name, height_m=0.0035, point_height=0)}
    for field, kind in (("f18", "detail"), ("fe8", "section"), ("f1e8", "auxiliary"),
                        ("f2b8", "orthographic"), ("f388", "miscellaneous")):
        f[field] = label_style(kind=kind, font_name=font_name)
    return f


def detail_definitions(*, standard, font_name, line_style_name, language_id, print_widths_m,
                       exclusion_names, task_labels, cutlist_expressions):
    if type(standard) is not int or standard != 1:
        raise ValueError("only the recovered standard-1 construction profile is supported")
    if not isinstance(cutlist_expressions, Sequence) or isinstance(cutlist_expressions, (str, bytes, bytearray)) or len(cutlist_expressions) != 3:
        raise ValueError("three authored cut-list id expressions are required")
    task_array = string_array(values=task_labels)
    if task_array["n"] != 5:
        raise ValueError("the five authored task-column labels are required")
    names = string_array(values=exclusion_names)
    f = {
        "f08": 0.002, "f10": standard, "f13a0": "", "f28": 0.0025,
        "f30": 1, "f20": 0x144000, "f24": 2,
        "f3c": 1, "f14": 0, "f18": 1, "f1c": 0, "f34": 1,
        "f1388": 0, "fec": 2, "ff0": 3, "ff4": 4,
        "ff8": 1e-5, "f100": 1.4e-5, "f108": 2.5e-6,
        "f110": 2, "f114": 3, "f118": 4,
        "f120": 0.00017453292519943334, "f128": 0.0002443460952792067,
        "f130": 4.3633231299858336e-5, "f138": int(standard != 0),
        "f140": 0.0005, "f148": 0.008726646259971667,
        "fe8": 1, "f150": 0, "f154": 1, "f158": 1, "f164": 1, "f168": 1,
        "f16c": 1, "f170": 0, "f174": 0, "f40": 0,
        "f138c": 1, "f1390": 0, "f1394": 0, "f1398": 0,
        "f44": 0, "f48": 0, "fe0": -1, "fe2": -1, "f50": 1, "f4c": 0,
        "f2bc0": 0.008, "f2bc8": 0, "f2bd8": "", "f2be0": 0,
        "f2be8": "", "f2bf0": 1, "f178": 0, "f17c": 0,
        "f1a8": 0, "f1ac": 0, "f1b0": 0, "f1b4": 0, "f180": 1,
        "f184": 1, "f188": 1, "f18c": 1, "f190": 1, "f194": 1,
        "n58": names["n"], "f58": names["items"], "f198": 1, "f1a0": 0, "f1a4": 0,
        "fb8": task_array,
        "f90": character_format(font_name=font_name, height_m=0.0035, point_height=0),
        "f13b0": dimension_definitions(font_name=font_name, line_style_name=line_style_name),
        "f1f18": annotation_definitions(font_name=font_name, language_id=language_id),
        "f2410": table_definitions(font_name=font_name), "f2750": label_definitions(font_name=font_name),
        "f2e8": surface_finish_data(font_name=font_name), "f4d8": note_data(font_name=font_name),
        "f730": weld_data(font_name=font_name), "f9a0": gtol_data(font_name=font_name),
        "fb88": center_mark_data(font_name=font_name), "fcd8": datum_feature_data(font_name=font_name),
        "fde0": datum_target_data(font_name=font_name), "ff68": swift_options(),
        "fb0": print_widths(widths_m=print_widths_m), "f2bd0": 5000.0,
        "f2bf4": 3, "f2bf8": 1, "f2bfc": 0, "f2c00": 0, "f2c0c": 1,
        "f2c10": 0, "f54": 1, "f2c04": 1, "f2c08": 1, "f80": 1, "f88": 0.0025,
        "f2c18": 0.0085, "f2c20": 0.0085, "f2c28": 0.0085,
        "f2c30": 3.0, "f2c38": 3.0, "f2c40": 0, "f2c44": 0,
        "f2c48": -1, "f2c4c": 0, "f2c50": 0, "f2c54": 1, "f2c58": 1, "f2c5c": 1,
        "f98": 0, "fa0": character_format(font_name=font_name, height_m=-1, point_height=12),
        "fa8": character_format(font_name=font_name, height_m=-1, point_height=12),
        "f2c64": 0, "f2c68": 0, "f19c": 0,
        "f1bc": 1, "f1c0": "Plate,", "f1c8": "", "f1d0": "x", "f1d8": "x",
        "f1e0": 2, "f1e4": 3, "f1e8": 1, "f1f8": 1, "f1f0": "Sheet", "f1fc": 0,
        "f15c": 1, "f160": 1, "f218": 0,
        "f200": text(cutlist_expressions[0], "cut-list id expression"),
        "f208": text(cutlist_expressions[1], "cut-list id expression"),
        "f210": text(cutlist_expressions[2], "cut-list id expression"),
        "f220": 1, "f224": 0, "f2c6c": 0, "f21c": 0, "f1b8": 0,
    }
    for origin in (0x228, 0x288):
        f.update({f"f{origin + 0x20 * group + 4 * item:x}": 0 for group in range(3) for item in range(8)})
    return f
