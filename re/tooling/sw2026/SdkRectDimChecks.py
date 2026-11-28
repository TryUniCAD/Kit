from __future__ import annotations

from collections import Counter
from struct import pack

from SdkBlindPartChecks import index, name, node, require


def handle_index(handle, expected, prepared):
    fields = node(handle, "sgPointHandle").FieldsValue
    if prepared:
        return index(fields, "idx", "f18", 0x777F, expected)
    require(fields["idx"] == min(expected, 0x777F) and fields["f18"] == expected,
            "constructed point handle lost its actual local index")
    return expected


def dimensions(profile, model, vertices, ids, presentation, prepared):
    sketch = node(profile.FieldsValue["pd_f80"], "sgSketch")
    fields = sketch.FieldsValue["dims"]
    values = tuple(node(row["d"], "sgPntPntDist") for row in fields["val_g2"])
    logical = tuple(row["d"] for row in fields["log_g1"])
    display_list = node(fields["f118"], "suObList")
    displays = tuple(node(row["o"], "moDisplayDistanceDim_c") for row in display_list.FieldsValue["items"])
    require(fields["ng2"] == len(values) == len(displays) == display_list.FieldsValue["n"] == 2 and
            fields["nlog1"] == len(logical) == 4, "rectangle dimension or unary collection counts differ")
    require(all(not fields[key] for key in ("val_g1", "val_g3", "log_g2", "log_g3")), "rectangle acquired an unmodeled dimension group")
    point_counts, line_counts = Counter(), Counter()
    lengths = vertices[1][0] - vertices[0][0], vertices[2][1] - vertices[1][1]
    for ordinal, (value, display, expected_id, length) in enumerate(zip(values, displays, ids, lengths, strict=True)):
        parameter = node(value.FieldsValue["f28"], "moLengthParameter_c")
        require(value.FieldsValue["f50"] == expected_id and value.FieldsValue["f80"] == 1 and
                value.FieldsValue["f90"] == 2 and value.FieldsValue["fa0"] == 0 and
                value.FieldsValue["refcount"] == 0, "rectangle driver lost constructor mode or allocated identity")
        require(parameter.FieldsValue["f08"] == -1 and name(parameter) == f"D{ordinal + 1}" and
                parameter.FieldsValue["f58"] == length, "rectangle driving parameter lost name length or unassigned node identity")
        for key, expected in (("h1", ordinal), ("h2", ordinal + 1)):
            point_counts[handle_index(value.FieldsValue[key], expected, prepared)] += 1
        require([value.FieldsValue[key] for key in ("f180", "f184", "f1b8", "f1bc")] == [1, 1, 1, 0] and
                value.FieldsValue["plane"] is None and value.FieldsValue["dir"] == {"x": 0.0, "y": 0.0, "z": 0.0},
                "point distance changed its proved nonarc position mode")
        require(display.FieldsValue["n850"] == len(display.FieldsValue["f850"]) == 1, "rectangle display lost one retained handle")
        handle = node(display.FieldsValue["f850"][0]["o"], "moSkDimHandleValG2_c")
        require(handle.FieldsValue["ff0"] is sketch and handle.FieldsValue["ff8"] == ordinal and handle.FieldsValue["fe8"] is None,
                "rectangle display does not retain its actual sketch and value array slot")
        require(display.FieldsValue["f58"] == 10 + ordinal and display.FieldsValue["fad0"] == length and
                display.FieldsValue["f5b0"]["data"] == pack("<d", length), "rectangle annotation identity or computed value cache differs")
        text = presentation["width_text_m" if ordinal == 0 else "height_text_m"]
        require(display.FieldsValue["f6a0"]["f10"] == 18 and
                display.FieldsValue["f6a0"]["f38"] == {"x": text[0], "y": text[1], "z": 0.0},
                "rectangle dimension text lost its authored local coordinates or native kind")
        require(display.FieldsValue["f1014"] == (0x800 if presentation["route_centerline"] else 0) and
                display.FieldsValue["f8a4"] & 0x2000000, "rectangle routing or loader normalization differs")
    for ordinal, value in enumerate(logical):
        require(value["f80"] == (4 if ordinal % 2 == 0 else 5) and value["f90"] == 2 and
                value["fa0"] == 0xFFFE and value["f50"] == -1, "rectangle unary relation changed line axis or constructor identity")
        handle = node(value["h1"], "sgLineHandle")
        if prepared:
            index(handle.FieldsValue, "idx", "f18", 0x777F, ordinal)
        else:
            require(handle.FieldsValue["idx"] == ordinal and handle.FieldsValue["f18"] == ordinal,
                    "constructed unary relation has the wrong actual line slot")
        line_counts[ordinal] += 1
    require(all(row["point"]["f20"] == point_counts[ordinal] for ordinal, row in enumerate(sketch.FieldsValue["points"])) and
            all(row["line"]["f20"] == line_counts[ordinal] for ordinal, row in enumerate(sketch.FieldsValue["lines"])),
            "rectangle entity reference counts are not derived from actual constraint handle occurrences")
    require(model.FieldsValue["fd44"] == 12, "model annotation counter did not consume exactly two displays")
    return {"value_count": len(values), "axis_relation_count": len(logical), "display_count": len(displays),
            "dimension_ids": [value.FieldsValue["f50"] for value in values],
            "parameter_names": [name(node(value.FieldsValue["f28"], "moLengthParameter_c")) for value in values],
            "lengths_m": lengths, "actual_sketch_handles": True, "constraint_reference_counts": True,
            "point_reference_counts": [point_counts[ordinal] for ordinal in range(4)],
            "line_reference_counts": [line_counts[ordinal] for ordinal in range(4)],
            "annotation_ids": [display.FieldsValue["f58"] for display in displays],
            "conditional_wire_indices": prepared, "constructor_solver_state_only": True}
