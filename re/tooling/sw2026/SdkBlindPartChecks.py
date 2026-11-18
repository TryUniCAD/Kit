from __future__ import annotations

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


def require(value, message):
    if not value:
        raise ValueError(message)


def node(value, expected):
    require(type(value) is ArchiveNode and value.ClassValue == RuntimeClass(expected, 1),
            "prepared native graph has the wrong concrete owner: " + expected)
    return value


def text(value):
    require(type(value) is CStringValue, "prepared field is not a typed native string")
    return value.TextValue


def name(value):
    return node(value.FieldsValue["f18"], "moNodeName_c").FieldsValue["f08"]


def index(fields, short_name, long_name, marker, expected):
    short = fields[short_name]
    require(type(short) is int and short == min(expected, marker), "prepared compact index differs")
    if short == marker:
        require(long_name in fields and type(fields[long_name]) is int and fields[long_name] == expected,
                "prepared extended index differs")
    else:
        require(long_name not in fields, "prepared compact index acquired an unencoded extension")
    return expected


def geometry(sketch, vertices):
    fields = node(sketch, "sgSketch").FieldsValue
    require(fields["npoints"] == fields["nlines"] == len(fields["points"]) == len(fields["lines"]) == 4,
            "prepared rectangle does not have four actual points and lines")
    require("f138" not in fields and fields["f128"] == fields["f12c"] == 1,
            "ordinary rectangle acquired runtime-only profile state or changed constructor solver words")
    require(fields["f130"] == fields["f56c"] == fields["f140"]["f08"] == fields["f140"]["f0c"] == 5,
            "prepared rectangle allocation counters differ")
    handles = []
    for ordinal, (row, position) in enumerate(zip(fields["points"], vertices, strict=True)):
        point = row["point"]
        require(row["kind"] == 0 and point["pos"] == dict(zip(("x", "y"), position, strict=True)),
                "prepared rectangle position differs from neutral input")
        require(point["pflags"] == 0x1E and point["fe8"] == 2 and point["f0c"] == ordinal + 1,
                "prepared rectangle marker namespace or adjacency degree differs")
        expected = (0, 3) if ordinal == 0 else (ordinal - 1, ordinal)
        for key, target in zip(("h1", "h2"), expected, strict=True):
            handle = node(point[key], "sgLineHandle")
            index(handle.FieldsValue, "idx", "f18", 0x777F, target)
            handles.append(handle)
    for ordinal, row in enumerate(fields["lines"]):
        line = row["line"]
        require(row["flags"] == 0 and line["f08"] == line["f0c"] == ordinal + 1,
                "prepared rectangle line identities differ")
        index(line, "fc8_s", "fc8", 0xFFFF, ordinal)
        index(line, "fcc_s", "fcc", 0xFFFF, (ordinal + 1) % 4)
    require(len({id(handle) for handle in handles}) == 8, "endpoint handles lost their exclusive native identities")
    return {"point_count": 4, "line_count": 4, "endpoint_handles": 8,
            "positions": True, "ordered_endpoints": True, "creation_counters": True,
            "conditional_wire_fields": True, "runtime_profile_backlink_absent": True}


def driving_depth(feature, expected_depth, expected_id):
    fields = node(feature, "moExtrusion_c").FieldsValue
    end = node(fields["f818"], "moEndSpec_c")
    require(fields["f810"] == -1 and end.FieldsValue["f08"] == 1 and end.FieldsValue["f8c"] == 0,
            "prepared boss is not the selected ordinary forward blind path")
    display = node(end.FieldsValue["f18"], "moDisplayDistanceDim_c")
    handles = display.FieldsValue["f850"]
    require(display.FieldsValue["n850"] == len(handles) == 1, "driving display lost its one actual handle")
    handle = node(handles[0]["o"], "moFeatureDimHandle_c")
    dimension = node(handle.FieldsValue["ff0"], "ParallelPlaneDistanceDim_c")
    parameter = node(dimension.FieldsValue["f28"], "moLengthParameter_c")
    require(dimension.FieldsValue["f50"] == expected_id and parameter.FieldsValue["f08"] == -1,
            "driving dimension and parameter namespaces differ")
    require(name(parameter) == "D1" and parameter.FieldsValue["f58"] == expected_depth,
            "driving D1 depth differs from actual neutral length")
    return {"native_name": "D1", "length_m": expected_depth, "persistent_id": expected_id,
            "actual_feature_path": True, "actual_handle": True}


def self_file(header, request, model_name, config_name):
    own = node(header.FieldsValue["f38"], "moExtObject_c")
    shared = own.FieldsValue["shared"]
    path = node(shared["h18"], "moCStringHandle_c")
    title = node(shared["h10"], "moCStringHandle_c")
    require(text(path.FieldsValue["value"]) == request["output"]["path_name"] and
            text(title.FieldsValue["value"]) == model_name and shared["f20"] == 2,
            "prepared self identity differs from modeled part path or name")
    require(text(own.FieldsValue["refcfg"]["f08"]) == config_name and own.FieldsValue["refcfg"]["f10"] == 0,
            "prepared self identity lost the actual active configuration")
    require(shared["f28"] == request["provenance"]["created_at"] and own.FieldsValue["f60"] == request["output"]["saved_at"],
            "prepared self identity lost authored creation or save provenance")
    return {"exact_path": True, "native_part_kind": 2, "actual_configuration_name": config_name}
