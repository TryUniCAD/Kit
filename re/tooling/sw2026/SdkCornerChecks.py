from __future__ import annotations

from collections import Counter

from SdkBlindPartChecks import index, name, node, require


def corner(profile, origin, model, vertices, prepared):
    sketch = node(profile.FieldsValue["pd_f80"], "sgSketch")
    origin_sketch = node(origin.FieldsValue["pd_f80"], "sgSketch")
    fields = sketch.FieldsValue
    points, lines, dims = fields["points"], fields["lines"], fields["dims"]
    require(fields["npoints"] == len(points) == 5 and fields["nlines"] == len(lines) == 4,
            "the external origin must be a fifth point and not a fifth contour edge")
    require([row["kind"] for row in points] == [0, 0, 0, 0, 1], "external point row discriminant differs")
    require([row["point"]["pos"] for row in points[:4]] == [dict(zip("xy", value, strict=True)) for value in vertices],
            "anchor changed independently authored contour coordinates")
    require(points[0]["point"]["pos"] == points[4]["point"]["pos"] == {"x": 0.0, "y": 0.0},
            "corner and external origin positions differ")
    point = points[4]["point"]
    require(point["f0c"] == 5 and point["f08"] == 0 and point["fe4"] == 6 and point["fe8"] == 0 and
            point["h1"] is point["h2"] is None and point["f54"] & 3 == 0,
            "external point lost source constructor or insertion state")
    external = node(point["ext"], "sgExtEnt_c")
    wrapper = node(external.FieldsValue["f08"], "moSketchExtRef_w")
    selected = node(wrapper.FieldsValue["f58"], "moCompSketchEntHandle_c")
    copied = node(selected.FieldsValue["f58"], "moUnitComponent_c")
    require(copied is not model.FieldsValue["f990"] and copied.FieldsValue["owner"] is model,
            "external selection lost its separate same-owner unit component")
    require(selected.FieldsValue["ff0"] == {"f00": origin.FieldsValue["f08"], "f08": 2592000} and
            selected.FieldsValue["f100"] == origin_sketch.FieldsValue["points"][0]["point"]["f0c"] == 1,
            "external selection does not use actual origin identity and native empty-log creation time")
    origin_handle = node(selected.FieldsValue["f0f8"], "sgPointHandle")
    if prepared:
        index(origin_handle.FieldsValue, "idx", "f18", 0x777F, 0)
    else:
        require(origin_handle.FieldsValue["idx"] == origin_handle.FieldsValue["f18"] == 0 and
                origin_handle.FieldsValue["_point"].FieldsValue is origin_sketch.FieldsValue["points"][0]["point"],
                "constructed selection does not target actual local origin")
    require(external.FieldsValue["f28"] == "Point1@" + name(origin) and
            all(external.FieldsValue[key] is None for key in ("f10", "f18", "f20")),
            "external entity naming or ordinary optional-owner state differs")
    require(wrapper.FieldsValue["f08"] == 101 and wrapper.FieldsValue["f70"] == 19000 and
            wrapper.FieldsValue["has_f10"] == wrapper.FieldsValue["has_f18"] == 0 and
            wrapper.FieldsValue["f60"] is None and wrapper.FieldsValue["fb0"] == 0,
            "origin wrapper does not retain source-proven direct selection state")
    backup = node(wrapper.FieldsValue["fb8"], "moPointBackedUpData_c")
    require(backup.FieldsValue["f08"] == {"x": 0.0, "y": 0.0, "z": 0.0},
            "origin backup position was not derived in the actual matching support frame")
    require(dims["ng2"] == len(dims["val_g2"]) == 2 and dims["nlog1"] == len(dims["log_g1"]) == 4 and
            dims["nlog2"] == len(dims["log_g2"]) == 1, "anchor lost existing editable rectangle groups")
    relation = dims["log_g2"][0]["d"]
    require(relation["f80"] == 9 and relation["f90"] == 2 and relation["fa0"] == 0xFFFE and
            relation["f50"] == -1, "coincidence has an invented persistent identity or wrong native relation type")
    counts = Counter()
    for handle_name, ordinal in (("h1", 4), ("h2", 0)):
        handle = node(relation[handle_name], "sgPointHandle")
        if prepared:
            index(handle.FieldsValue, "idx", "f18", 0x777F, ordinal)
        else:
            require(handle.FieldsValue["idx"] == handle.FieldsValue["f18"] == ordinal and
                    handle.FieldsValue["_point"].FieldsValue is points[ordinal]["point"], "coincidence actual point handle differs")
        counts[ordinal] += 1
    for ordinal, row in enumerate(dims["val_g2"]):
        value = node(row["d"], "sgPntPntDist")
        parameter = node(value.FieldsValue["f28"], "moLengthParameter_c")
        length = vertices[ordinal + 1][ordinal] - vertices[ordinal][ordinal]
        require(name(parameter) == f"D{ordinal + 1}" and parameter.FieldsValue["f58"] == length and
                value.FieldsValue["f50"] == 19 + ordinal, "anchor changed actual named length drivers")
        for handle_name, expected in (("h1", ordinal), ("h2", ordinal + 1)):
            handle = node(value.FieldsValue[handle_name], "sgPointHandle")
            if prepared:
                index(handle.FieldsValue, "idx", "f18", 0x777F, expected)
            else:
                require(handle.FieldsValue["idx"] == handle.FieldsValue["f18"] == expected, "driver point index changed")
            counts[expected] += 1
    require([row["point"]["f20"] for row in points] == [counts[ordinal] for ordinal in range(5)] and
            [row["line"]["f20"] for row in lines] == [1] * 4,
            "point and line use counts are not computed from actual relation occurrences")
    require(fields["f140"]["f08"] == 6 and origin_sketch.FieldsValue["points"][0]["point"]["f08"] == 1,
            "anchor did not update the actual insertion counter or selected origin permanent mark")
    return {"contour_points": 4, "external_points": 1, "lines": 4, "point_creation_next": 6,
            "value_dimensions": 2, "axis_relations": 4, "origin_relations": 1,
            "point_use_counts": [counts[ordinal] for ordinal in range(5)], "line_use_counts": [1] * 4,
            "origin_feature_id": origin.FieldsValue["f08"], "origin_point_mark": 1,
            "origin_creation_time": 2592000, "actual_owner_aliases": True, "prepared": prepared}
