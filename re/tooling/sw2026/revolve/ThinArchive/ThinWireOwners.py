from math import isclose

from AuditRevEndOwners import (
    ArchiveNode, IndexFeatures, NativeNodeSpan, NativeRows, ReadNativeName, ReadParents,
    ReadRevAxisRef, RequireNative, observe_ends, point, require,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import ReadPrismFrame
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimGroups import CheckDimGroups
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimRows import ReadDimRows
from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckLineEntity import CheckLineEntity
from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckLineScope import CheckLineScope
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineIndex import LineIndex
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.ReadAxisLine import ReadAxisLine
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.ReadAxisPoint import ReadAxisPoint

THIN_FEATURE = "moRevolutionThin_c"
THIN_SPEC = "moThinSpec_c"
REF_CLASSES = frozenset(("moThinClosingSurfIdRep_c", "moThinOffsetSurfIdRep_c"))
RADIUS_CLASS = "ThreeDRadiusDim_c"


def span(link, node):
    row = NativeNodeSpan(link, node)
    return (row["class"], row["object_index"], row["offset"], row["end"])


def close(left, right):
    return isclose(left, right, rel_tol=2e-7, abs_tol=1e-12)


def require_positions(points, expected, label):
    require(all(close(a, b) for a, b in zip(points, expected, strict=True)), label)


def check_open_profile(link, feature, definition, native_profile):
    (profile,) = ReadParents(feature)
    profile = RequireNative(profile, "moProfileFeature_c")
    sketch = RequireNative(profile.FieldsValue["pd_f80"], "sgSketch")
    root = link.ConfigValue.RootValue
    selected = ReadRevAxisRef(feature, profile, root)
    frame = ReadPrismFrame(profile, root, IndexFeatures(link), FrontOnly=False)
    frame_points = tuple(point(value) for value in (frame.origin, frame.x_axis, frame.y_axis, frame.z_axis))
    require(list(frame_points) == native_profile["frame_points"], "thin discovery plane changed")
    fields = sketch.FieldsValue
    CheckLineScope(fields, HasDrivers=True)
    dims = NativeRecord(fields["dims"])
    CheckDimGroups(dims)
    require(not ReadDimRows(dims, "ng2", "val_g2") and not ReadDimRows(dims, "nlog1", "log_g1")
            and IsLineState(dims["f118"]), "thin sketch has added dimension or relation owners")
    lines = NativeRows(fields["lines"])
    points = NativeRows(fields["points"])
    require(fields["nlines"] == len(lines) == 2 and fields["npoints"] == len(points) == 4,
            "thin sketch line or point inventory differs")
    axis_line = ReadAxisLine(lines[selected.IndexValue], selected)
    profile_index = next(index for index in range(len(lines)) if index != selected.IndexValue)
    profile_row = lines[profile_index]
    body_line = NativeRecord(profile_row["line"])
    CheckLineEntity(body_line, FlagsValue=68)
    require(profile_row["flags"] == 0 and body_line["fd0"] == 1 and body_line["fd4"] == body_line["fe8"] == 0,
            "thin sketch body line does not have ordinary open incidence")
    body_ends = tuple(LineIndex(body_line, key + "_s", key, 65535) for key in ("fc8", "fcc"))
    axis_ends = axis_line.StartValue, axis_line.EndValue
    require(sorted((*body_ends, *axis_ends)) == list(range(4)), "thin centreline shares body endpoints")
    positions = {
        role: [ReadAxisPoint(points[index], index, owner).PositionValue for index in indices]
        for role, indices, owner in (("body", body_ends, profile_index), ("axis", axis_ends, selected.IndexValue))
    }
    for a, b in zip(positions["axis"], definition["axis"]["points"], strict=True):
        require_positions(a, [1000 * value for value in b[:2]], "stored centreline differs from native selection")
    (native_line,) = [row for row in native_profile["segments"] if not row["construction"]]
    require(native_line["kind"] == "line", "native profile did not report an open body line")
    for a, p in zip(positions["body"], (native_line["start"], native_line["end"]), strict=True):
        require_positions(a, [1000 * value for value in p], "open profile differs from its authored axial line")
    return {"profile": span(link, profile), "profile_id": NativeNodeId(profile), "sketch": span(link, sketch),
            "frame": frame_points, "points_mm": positions,
            "body_line": (profile_index, body_line["f08"], *body_ends),
            "axis_line": (selected.IndexValue, selected.MarkValue, *axis_ends)}


def length_owner(link, value, radial=False):
    display = RequireNative(value, "moDisplayRadialDim_c" if radial else "moDisplayDistanceDim_c")
    (row,) = NativeRows(display.FieldsValue["f850"])
    handle = RequireNative(row["o"], "moFeatureDimHandle_c")
    dimension = RequireNative(handle.FieldsValue["ff0"], RADIUS_CLASS if radial else "ParallelPlaneDistanceDim_c")
    param = RequireNative(dimension.FieldsValue["f28"], "moLengthParameter_c")
    require(display.FieldsValue["n850"] == 1 and handle.FieldsValue["fe8"] is None
            and handle.FieldsValue["f100"] is None and param.FieldsValue["f68"] == 0
            and param.FieldsValue["f20"] == "" and param.FieldsValue["f48"] is None,
            "thin display uses an alternate handle or parameter")
    fields = dimension.FieldsValue
    return {"name": ReadNativeName(param), "metres": RequireScalar(param.FieldsValue["f58"]),
            "dimension_id": fields["f50"], "anchor": [list(fields[key][axis] for axis in "xyz") for key in ("f80", "fa0")],
            "frame_present": (fields["has_fe0"], fields["has_ff0"]),
            "chain": [span(link, n) for n in (display, handle, dimension, param)]}


def match_driver(driver, measurement, value_key):
    require(driver["name"] == measurement["name"].split("@", 1)[0] and measurement["editable"]
            and close(driver[value_key] * measurement["display_scale"], measurement["value"]),
            "typed driver differs from native editable dimension")


def check_walls(thin, mode, native, profile, link, *, place=None):
    f = thin.FieldsValue
    first, second = (length_owner(link, f[slot]) for slot in ("f08", "f10"))
    require(all(a[1] != b[1] for a, b in zip(first["chain"], second["chain"], strict=True)),
            "wall display, handle, dimension or parameter aliases its other side")
    match_driver(first, native["drivers"]["wall1"], "metres")
    w1, w2 = first["metres"], second["metres"]
    require_positions((w1, w2), native["definition"]["wall_getters_m"], "actual thickness differs from native getters")
    require((w2 > 0) == (mode == 3) and w1 > 0, "thin wall activation state differs")
    x = profile["points_mm"]["body"][0][0] / 1000
    y = sum(row[1] for row in profile["points_mm"]["body"]) / 2000
    start, end = {0: (x, x + w1), 1: (x, x - w1), 2: (x - w1 / 2, x + w1 / 2), 3: (x, x + w1)}[mode]
    place = place or check_wall_points
    place(first, start, end, y)
    if mode == 3:
        match_driver(second, native["drivers"]["wall2"], "metres")
        place(second, x, x - w2, y)
    else:
        require(second["frame_present"] == (0, 0) and "wall2" not in native["drivers"],
                "inactive second wall has an unexpected editable or geometric owner")
    return {"f08": first, "f10": second, "active": ("f08", "f10") if mode == 3 else ("f08",)}


def check_wall_points(row, start, end, y):
    require(row["frame_present"] == (1, 1), "live wall display lost its actual placement")
    for point_value, expected in zip(row["anchor"], ((start, y, 0), (end, y, 0)), strict=True):
        require_positions(point_value, expected, "native wall endpoints differ from the signed profile span")


def face_references(link, feature):
    by_ref, rows_by_rep, ext_objects = {}, {}, set()
    for entry in link.ResolvedValue.MapValue.EntriesValue:
        node = entry.EntryValue
        if not isinstance(node, ArchiveNode) or node.ClassValue.NameValue != "moFaceRef_c":
            continue
        face = []
        for row_index, row in enumerate(NativeRows(node.FieldsValue["f10"])):
            rep = row["f08"]
            if not isinstance(rep, ArchiveNode) or rep.ClassValue.NameValue not in REF_CLASSES:
                continue
            f = rep.FieldsValue
            keeper = NativeRecord(f["f10"])
            source = RequireNative(keeper["f10"], "moFR_c")
            key = NativeRecord(source.FieldsValue["f10"])
            external = RequireNative(source.FieldsValue["f08"], "moExtObject_c")
            require(keeper["f08"] is None and key["f00"] == NativeNodeId(feature),
                    "thin surface ID points outside the actual revolve producer")
            require(NativeRecord(external.FieldsValue["refcfg"])["f08"] == "Default",
                    "thin surface ID points outside the current native configuration")
            ext_objects.add(id(external))
            rep_index = rep.IndexValue
            rows_by_rep.setdefault(rep_index, (span(link, rep), f["f38"], f.get("f3c"), key["f00"]))
            face.append((row_index, rep_index))
        if face:
            by_ref[node.IndexValue] = face
    require(len(rows_by_rep) == 6 and len(by_ref) == 4 and len(ext_objects) == 1,
            "disclosed saved thin surface identity inventory changed")
    require(tuple(by_ref.values())[:2] == tuple(by_ref.values())[2:], "saved duplicate face refs stopped aliasing their IDs")
    return {"surface_ids": tuple(rows_by_rep.values()), "face_ref_rows": by_ref}


def inspect_thin(link, native, profile_spec, is_edited):
    (feature,) = tuple(node for node in link.ResolvedValue.RootsValue
                       if isinstance(node, ArchiveNode) and node.ClassValue.NameValue == THIN_FEATURE)
    f = feature.FieldsValue
    definition = native["definition"]
    require(definition["is_thin"] and definition["is_boss"] and definition["type"] == 0
            and ReadNativeName(feature) == "ThinBossRevolve" and f["f828"] == 5
            and f["f824"] == int(definition["reverse"]), "actual saved thin or angular branch differs")
    angles = observe_ends(link, feature)
    require(angles["angles"]["f20"] is None and angles["end_words"]["f08"] == 1
            and not any(angles["feature_legacy_display_slots"].values()), "disclosed thin uses an alternate angular owner")
    match_driver(angles["angles"]["f18"], native["drivers"]["angle"], "radians")
    thin = RequireNative(f["f8f0"], THIN_SPEC)
    mode = thin.FieldsValue["f28"]
    require(type(mode) is int and mode in range(4) and mode == definition["wall_mode"],
            "raw thin direction word differs from native enum")
    profile = check_open_profile(link, feature, definition, profile_spec)
    walls = check_walls(thin, mode, native, profile, link)
    radial = thin.FieldsValue["f48"]
    require((radial is not None) == is_edited, "native edit changed the expected inactive radius inventory")
    radius = length_owner(link, radial, radial=True) if radial is not None else None
    if radius is not None:
        require(radius["metres"] == 0 and radius["name"] not in {driver["name"].split("@", 1)[0]
                                                               for driver in native["drivers"].values()},
                "saved radial dimension became an active native driver")
    (atom_row,) = NativeRows(NativeRecord(f["f528"])["items"])
    atom = RequireNative(atom_row["o"], "moAtom_c")
    require(any(entry.EntryValue is atom for entry in link.ConfigValue.MapValue.EntriesValue),
            "thin body atom backlink is outside the inherited configuration")
    return {"thin_spec": span(link, thin), "thin_spec_words": {key: thin.FieldsValue[key] for key in (
                "f2c", "f30", "f38", "f28", "f40", "f50", "f54")}, "revolve": angles, "profile": profile,
            "walls": walls, "radius": radius, "atom": span(link, atom), "face_refs": face_references(link, feature)}
