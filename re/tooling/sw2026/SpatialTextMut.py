from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import replace
from math import isfinite

from convert.adapters.solidworks.Archive.Construction.Part.EmitPartStreams import EmitPartStreams
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Container.Container import BuildSldprt


def require(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


def concrete(value, class_name):
    require(type(value) is ArchiveNode and type(value.ClassValue) is RuntimeClass
            and value.ClassValue == RuntimeClass(class_name, 1),
            "spatial text requires the concrete ordinary class " + class_name)
    return value


def point3(value):
    require(type(value) in (list, tuple) and len(value) == 3,
            "spatial text requires three explicit world coordinates")
    require(all(type(item) in (float, int) and isfinite(item) for item in value),
            "spatial text coordinates must be finite numbers without booleans")
    return tuple(float(item) for item in value)


def actual_displays(profile):
    profile = concrete(profile, "moProfileFeature_c")
    sketch = concrete(profile.FieldsValue["pd_f80"], "sgSketch")
    dims = sketch.FieldsValue["dims"]
    require(isinstance(dims, Mapping), "spatial text needs the actual sketch dimension manager")
    displays = concrete(dims["f118"], "suObList").FieldsValue
    rows = displays["items"]
    values = dims["val_g2"]
    require(type(displays["n"]) is int and type(dims["ng2"]) is int
            and displays["n"] == dims["ng2"] == len(rows) == len(values) == 2,
            "spatial text only owns the two complete rectangle driver displays")
    result = []
    for index, (row, value_row) in enumerate(zip(rows, values, strict=True)):
        display = concrete(row["o"], "moDisplayDistanceDim_c")
        fields = display.FieldsValue
        require(type(fields["n850"]) is int and fields["n850"] == len(fields["f850"]) == 1,
                "spatial text display has another actual dimension handle")
        handle = concrete(fields["f850"][0]["o"], "moSkDimHandleValG2_c")
        require(handle.FieldsValue["ff0"] is sketch and type(handle.FieldsValue["ff8"]) is int
                and handle.FieldsValue["ff8"] == index,
                "spatial text display targets a different actual sketch or value")
        dimension = concrete(value_row["d"], "sgPntPntDist")
        parameter = concrete(dimension.FieldsValue["f28"], "moLengthParameter_c")
        result.append((display, dimension, parameter))
    return tuple(result)


def place_text_mut(display, xyz):
    display = concrete(display, "moDisplayDistanceDim_c")
    xyz = point3(xyz)
    text = display.FieldsValue["f6a0"]
    require(isinstance(text, MutableMapping) and type(text["f10"]) is int and text["f10"] == 18,
            "spatial text needs the actual embedded distance moDimText_c")
    old = text["f38"]
    require(isinstance(old, Mapping) and set(old) == {"x", "y", "z"},
            "spatial text position has an unsupported geometry representation")
    _ = point3(tuple(old[key] for key in ("x", "y", "z")))
    text["f38"] = dict(zip(("x", "y", "z"), xyz, strict=True))


def text_rows(profile):
    result = []
    for display, dimension, parameter in actual_displays(profile):
        point = display.FieldsValue["f6a0"]["f38"]
        result.append({"xyz_m": list(point3(tuple(point[key] for key in ("x", "y", "z")))),
                       "value_id": dimension.FieldsValue["f50"],
                       "annotation_id": display.FieldsValue["f58"],
                       "length_m": parameter.FieldsValue["f58"]})
    return result


def compose_text_mut(child, settings, keys, xyz_values):
    require(type(xyz_values) is list and len(xyz_values) == 2,
            "spatial text needs exactly two explicit rectangle text points")
    points = tuple(point3(value) for value in xyz_values)
    displays = actual_displays(child.ProfileValue.ProfileValue)
    before = text_rows(child.ProfileValue.ProfileValue)
    require(all(list(value[:2]) == row["xyz_m"][:2] for value, row in zip(points, before, strict=True)),
            "spatial text operation preserves the qualified planar placement")
    for (display, _, _), xyz in zip(displays, points, strict=True):
        place_text_mut(display, xyz)
    streams, config, resolved = EmitPartStreams(
        child.SystemValue, child.ResolvedValue.RootsValue,
        (child.HeaderValue, child.TopHeader, child.ManagerHeader), child.DefinitionValue,
        settings, child.PlanValue, keys)
    changed = sorted(name for name in streams if streams[name] != child.StreamsValue[name])
    has_change = any(row["xyz_m"] != list(point) for row, point in zip(before, points, strict=True))
    require(changed == (["Contents/Config-0-ResolvedFeatures"] if has_change else []),
            "spatial text changed a stream outside its actual resolved owner")
    updated = replace(child, ConfigValue=config, ResolvedValue=resolved,
                      StreamsValue=streams, BytesValue=BuildSldprt(streams, FormatVersion=4))
    return updated, before, text_rows(updated.ProfileValue.ProfileValue), changed
