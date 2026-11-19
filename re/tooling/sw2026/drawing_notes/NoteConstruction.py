from __future__ import annotations

from math import hypot, isfinite

from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeObList import MakeObList
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import MakePoint
from convert.adapters.solidworks.Archive.Construction.Geometry.IdentityXform import IdentityXform
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from interchange.document.Models.Drawing.DrawingNote import DrawingNote


def node(name, fields):
    return ArchiveNode(RuntimeClass(name, 1), fields)


def object_rows(values):
    items = tuple({"o": value} for value in values)
    return {"n": len(items), "items": items}


def fresh_width():
    return {"f06": 0, "f00": -1.0}


def zero_line_metrics():
    return {"f00": 0.0, "f04": 0.0, "f08": 0.0}


def paragraph(style, *, line):
    spacing = style["f78"]
    para_spacing = spacing if spacing < 1.0 and (not line or spacing > 0.0) else 0.001
    return {
        "f00": 0,
        "f08": 0.0,
        "f10": 0.0,
        "f18": 0.01,
        "f20": 0,
        "f24": 0,
        "f28": "$$.",
        "f30": 0,
        "f34": 0,
        "f38": 0,
        "f40": 0.0,
        "f48": 0.0,
        "f50": 0,
        "f58": para_spacing,
        "f60": 0.001,
        "f68": 0,
        "f6c": -1,
    }


def character(code_unit, index):
    return node("moTextDataChar_c", {
        "f08": index,
        "f0c": index,
        "f10": 0,
        "f20": zero_line_metrics(),
        "f2c": 0.0,
        "f30": 1,
        "f34": 0,
        "f38": 0.0,
        "f40": code_unit,
    })


def note_text_list(text, style):
    units = text.encode("utf-16-le")
    code_units = tuple(int.from_bytes(units[offset:offset + 2], "little") for offset in range(0, len(units), 2))
    if not code_units:
        raise ValueError("plain note requires one nonempty line")
    line = node("moTextDataLineHead_c", {
        "f08": 0,
        "f0c": len(code_units) - 1,
        "f14": zero_line_metrics(),
        "f10": 0,
        "f30": paragraph(style, line=True),
        "f38": zero_line_metrics(),
        "f48": None,
        "f50": -1,
        "f58": 1.0,
        "f64": 0,
    })
    glyphs = tuple(character(code_unit, index) for index, code_unit in enumerate(code_units))
    return node("moGenTextDataList_c", {
        "f10": node("suObArray", object_rows((line, *glyphs))),
        "f18": {"f00": 0.0, "f08": 0.0, "f10": 0.0, "f18": 0.0},
        "f128": 0,
    })


def generic_text(note, details, style):
    text = note.TextValue
    point = note.PositionValue
    position = (point.x, point.y, point.z)
    if not text or any(not value.isprintable() or value in "<>" for value in text):
        raise ValueError("fresh note requires one ordinary unformatted line")
    if not all(isfinite(value) for value in position):
        raise ValueError("plain note position must be finite")
    flags = (1 << 0) | (1 << 16) | (1 << 17) | (1 << 18)
    if details["f20"] & 0x10000:
        raise ValueError("fresh note candidate excludes the document uppercase reparse option")
    return node("moGenericText_c", {
        "f08": text,
        "f38": MakePoint(XValue=point.x, YValue=point.y, ZValue=point.z),
        "f10": 21,
        "f18": None,
        "f20": style["f1c"],
        "f50": MakePoint(),
        "f68": 1.0,
        "n90": 0,
        "f98": (),
        "fc4": 0,
        "fa0": 0,
        "fd0": 0,
        "fd8": 1e-6,
        "fe0": 1e-6,
        "f24": 0,
        "f0f0": MakeObList(),
        "f118": 0,
        "f120": 0,
        "f124": 0,
        "f128": 1.0,
        "f130": 0,
        "f158": note_text_list(text, style),
        "f160": flags,
        "f170": None,
        "f188": paragraph(style, line=False),
    })


def note_data(text):
    return node("moNoteData_c", {
        "f08": -1,
        "f0c": 0,
        "f18": None,
        "f20": "",
        "f28": 1 << 30,
        "f2c": 0,
        "f50": 0,
        "f48": None,
        "f58": MakeObList(),
        "f68": (),
        "n70": 0,
        "f80": 0,
        "f88": None,
        "f98": text,
    })


def component_note(data, version):
    return node("moCompNote_c", {
        "f18": 0,
        "f1c": 0,
        "f20": 0,
        "f30": 0,
        "f34": 0,
        "f48": 0,
        "f4c": version,
        "f58": None,
        "f68": 0,
        "f70": 0,
        "f84": 0,
        "f90": -1,
        "f94": -1,
        "f98": -1,
        "f9c": -1,
        "fa0": 0,
        "has_fb0": 0,
        "has_fb8": 0,
        "has_fc0": 0,
        "has_fc8": 0,
        "has_fd0": 0,
        "fe8": data,
        "ff8": None,
        "f100": 0,
    })


def display_base(component, style, version):
    points = tuple({"p": MakePoint()} for _ in range(4))
    vectors = tuple({"v": MakePoint(YValue=1.0)} for _ in range(2))
    frame = style["f34"]
    return {
        "f50": 0,
        "f30": None,
        "f40": None,
        "f48": component,
        "f54": 0,
        "f11c": 0,
        "f08": {
            "f00": 65535,
            "f02": 0,
            "f04": 3,
            "f08": {"f00": (1 << 32) - 1, "f04": 0, "f08": fresh_width()},
        },
        "f68": MakeObList(),
        "fb0": MakeObList(),
        "f58": 0,
        "ff8": None,
        "linked": 0,
        "f118": version,
        "f390": style["f20"],
        "f3e0": 0x82 | (1 << 19),
        "f290": MakePoint(),
        "has_f298": 0,
        "has_f288": 0,
        "f3f8": None,
        "f400": MakePoint(),
        "f2a0": IdentityXform(),
        "f2b0": (),
        "n2b0": 0,
        "has_f2c0": 0,
        "f2c8": 0.0,
        "has_f2d0": 0,
        "f3c0": (),
        "n3d0": 0,
        "f2d8": None,
        "f3b8": -1.0,
        "f2e0": (),
        "n2e8": 0,
        "f2f0": 1,
        "f2f8": dict(style["f2c"]) if frame else fresh_width(),
        "f2f4": frame,
        "f304": 1,
        "f30c": dict(style["f38"]),
        "f308": style["f40"],
        "f300": 0,
        "f314": 0,
        "f334": -1,
        "f338": -1,
        "has_f4a0": 0,
        "f318": 1,
        "f31c": 0,
        "f320": fresh_width(),
        "f328": 0,
        "f32c": 0,
        "f4a8": (),
        "n4a8": 0,
        "has_f4b8": 0,
        "n4f0": len(points),
        "f4f0": points,
        "n550": len(vectors),
        "f550": vectors,
    }


def display_note(component, style, version):
    bits = sum(1 << bit for bit in (0, 20, 27, 28, 29))
    flags = ({"v": bits >> 32}, {"v": bits & ((1 << 32) - 1)})
    return node("moDisplayNote_c", display_base(component, style, version) | {
        "f644": 1,
        "f648": int(style["f24"] == 1),
        "f64c": 0,
        "f628": MakePoint(),
        "f630": 0.0,
        "f690": style["f5c"],
        "f694": style["f58"],
        "f6a0": None,
        "f658": "",
        "f660": "",
        "f668": "",
        "f6b8": None,
        "f590": None,
        "f768": flags,
        "n768": len(flags),
        "f5a0": None,
        "f698": style["f68"],
        "f6d8": "",
        "f6e0": node("moFavoriteHandle_c", {"f08": 2, "f0c": -1, "f10": 0}),
        "f640": 0,
        "f5b0": None,
        "f5b8": 0,
        "f5bc": 0,
        "f710": style["f70"],
        "f5c0": 0,
        "f770": 0,
        "f784": -1,
        "f788": -1,
        "f78c": -1,
        "f790": None,
        "f6c0": None,
    })


def construct_local_hierarchy(note, details, version):
    if type(note) is not DrawingNote or version != 19000:
        raise ValueError("plain-note research requires typed note intent and the 2026 serializer")
    style = details["f1f18"]["f418"]
    text = generic_text(note, details, style)
    data = note_data(text)
    component = component_note(data, version)
    return display_note(component, style, version)



def register_origin_anchor(display, position):
    length = hypot(position.x, position.y, position.z)
    if length == 0.0:
        raise ValueError("origin-anchor comparison needs a distinct text position")
    data = display.FieldsValue["f48"].FieldsValue["fe8"]
    absolute = node("moAbsolutePoint_c", {
        "f08": MakePoint(),
        "f28": MakePoint(),
        "f20": 0,
        "f50": None,
        "f58": MakePoint(),
        "f70": MakePoint(),
        "f88": 0,
    })
    cache = node("moAttachPointData_c", {
        "f08": MakePoint(),
        "f20": MakePoint(),
        "f38": None,
        "f40": 0.0,
        "f48": 0.0,
    })
    data.FieldsValue["f58"] = object_rows((absolute,))
    display.FieldsValue.update(
        has_f298=1,
        f298=object_rows((cache,)),
        f630=length,
        f628=MakePoint(XValue=position.x/length, YValue=position.y/length, ZValue=position.z/length),
    )



def publish_first_note_identity(model, folder, display, language_id):
    owners = folder.FieldsValue["f358"]
    index = model.FieldsValue["fd44"]
    data = display.FieldsValue["f48"].FieldsValue["fe8"]
    if (
        language_id != 1033 or owners["n"] != 0 or owners["items"]
        or type(index) is not int or not 10 <= index < 0x7FFFFFFF
        or display.FieldsValue["f58"] != 0 or data.FieldsValue["f18"] is not None
    ):
        raise ValueError("first-note identity requires the fresh English note owners")
    display.FieldsValue["f58"] = index
    model.FieldsValue["fd44"] = index + 1
    data.FieldsValue["f18"] = node("moNodeName_c", {"f08": "DetailItem" + str(owners["n"] + 1)})
