from struct import unpack

from convert.adapters.base.SafeParsing import ParseUntrusted


def _dimension(*, value, display, sketch):
    parameter = value["f28"]
    handle = display["f850"][0]["o"]
    return {
        "value_class": value.cls,
        "id": value["f50"],
        "parameter_class": parameter.cls,
        "parameter_id": parameter["f08"],
        "name": parameter["f18"]["f08"],
        "value_m": parameter["f58"],
        "endpoint_slots": [value[key]["idx"] for key in ("h1", "h2")],
        "driven": value["f94"],
        "display_id": display["f58"],
        "display_class": display.cls,
        "display_handle_class": handle.cls,
        "display_handle_slot": handle["ff8"],
        "display_owns_sketch": handle["ff0"] is sketch,
        "display_value_m": unpack("<d", display["f5b0"]["data"])[0],
        "display_text_m": [display["f6a0"]["f38"][key] for key in ("x", "y", "z")],
        "display_parameter": display["f8a8"],
        "display_offset_m": display["f8b0"],
        "route_centerline": bool(display["f1014"] & 0x800),
    }


def read_rectangle(*, archive, model, profiles):
    profile = next(node for node in profiles if node.cls == "moProfileFeature_c")
    sketch = profile["pd_f80"]
    dims = sketch["dims"]
    values = (row["d"] for row in dims["val_g2"])
    displays = (row["o"] for row in dims["f118"]["items"])
    root = ParseUntrusted(archive.require("swXmlContents/KeyWords")[1:])
    feature = next(node for node in root if node.get("id") == str(profile["f08"]))
    return {
        "values": [_dimension(value=value, display=display, sketch=sketch) for value, display in zip(values, displays, strict=True)],
        "logical_types": [row["d"]["f80"] for row in dims["log_g1"]],
        "logical_line_slots": [row["d"]["h1"]["idx"] for row in dims["log_g1"]],
        "point_references": [row["point"]["f20"] for row in sketch["points"]],
        "line_references": [row["line"]["f20"] for row in sketch["lines"]],
        "next_display_id": model["fd44"],
        "keywords": {node.attrib["Name"]: float(node.text) for node in feature if node.tag == "Dimension"},
    }
