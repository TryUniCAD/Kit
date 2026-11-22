from math import atan2, degrees, hypot, isclose, pi

from EllipseArchiveGrammar import HANDLE, POINT_INDEX_FIELDS
from EllipseModel import require
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import ReadPrismFrame
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative

POINT_ROLES = ("Center", "Major", "Minor", "OppositeMajor", "OppositeMinor")
COMMON_FIELDS = ("f08", "f0c", "f20", "f30", "f34", "f38", "f50", "f54", "f56",
                 "dflt", "ext", "has_name", "f68", "f74", "f78", "vis", "lw", "group")


def xy_meter(point):
    return tuple(point["pos"][axis] for axis in ("x", "y"))


def vector3(vector):
    return (vector.x, vector.y, vector.z)


def difference(first, second):
    return tuple(a - b for a, b in zip(first, second, strict=True))


def dot(first, second):
    return sum(a * b for a, b in zip(first, second, strict=True))


def near(actual, desired):
    return all(isclose(a, b, rel_tol=0.0, abs_tol=1e-15) for a, b in zip(actual, desired, strict=True))


def event_fields(record):
    return {key: value for key, value in record.items() if key not in ("node", "scope")}


def owner_record(link, node):
    return dict(NativeNodeSpan(link, node)) | {"schema": node.ClassValue.SchemaValue}


def point_row(row, record, ordinal):
    point = row["point"]
    require(record["scope"] is point and record["map_after"] >= record["map_before"],
            "sketch point event does not own its decoded row")
    return {
        "ordinal": ordinal, "row_kind": row["kind"], "persistent_words": [point["f08"], point["f0c"]],
        "coordinates_m": xy_meter(point), "wire": event_fields(record),
        "handle_index": point["h1"].IndexValue if point["h1"] is not None else None,
        "value_fields": {key: point[key] for key in ("pflags", "fe4", "fe8", "fec", "f108", "ff0")},
    }


def resolve_row(link, sketch, observed):
    fields = sketch.FieldsValue
    require(fields["nellipses"] == len(fields["ellipses"]) == 1 and fields["npoints"] == len(fields["points"]) == 6
            and not any(fields[key] for key in ("arcs", "lines", "splines", "parabolas", "texts",
                                               "planes", "hatches", "offsets", "sketch_offsets"))
            and not any(value for key, value in fields["dims"].items() if key != "f118")
            and not any(fields["coinc"].values()) and not fields["f598"]["n"] and not fields["f580"]["f40"]["n"],
            "typed sketch does not contain the ordinary free full ellipse")
    (row,) = fields["ellipses"]
    ellipse = row["ellipse"]
    (body,) = observed["inline"]
    require(row["flags"] == 0 and body["scope"] is ellipse and body["node"] is sketch
            and body["map_before"] == body["map_after"] and ellipse["group"] is ellipse["ext"] is None,
            "inline ellipse lost its physical sketch role")
    points = fields["points"]
    records = [record for record in observed["points"] if record["node"] is sketch]
    members = [point_row(row, record, i) for i, (row, record) in enumerate(zip(points, records, strict=True))]
    ordinals = [ellipse[key + "_s"] for key in POINT_INDEX_FIELDS]
    seam = ellipse["fc8_s"]
    require(ellipse["fcc_s"] == seam and set((*ordinals, seam)) == set(range(len(points)))
            and not any(key in ellipse for key in ("fc8", "fcc", *POINT_INDEX_FIELDS)),
            "ordinary complete ellipse requires a shared seam and five distinct short point ordinals")
    bindings = dict(zip(POINT_ROLES, ordinals, strict=True)) | {"Seam": seam}
    (handle_event,) = observed["handles"]
    handle = RequireNative(points[seam]["point"]["h1"], HANDLE)
    (class_slot,) = [entry.IndexValue for entry in link.ResolvedValue.MapValue.EntriesValue
                     if entry.EntryValue is handle.ClassValue]
    require(handle_event["node"] is handle and not any(row["point"]["h2"] for row in points)
            and all(item["handle_index"] is None for item in members if item["ordinal"] != seam)
            and handle.FieldsValue.keys() == {"idx", "f1c", "f08"}
            and 0 <= handle.FieldsValue["idx"] < fields["nellipses"]
            and fields["ellipses"][handle.FieldsValue["idx"]]["ellipse"] is ellipse,
            "sketch seam handle does not select the actual ellipse row")
    return {
        "owner": owner_record(link, sketch), "wire": event_fields(body),
        "points": members, "point_bindings": bindings, "row_flags": row["flags"],
        "segment_fields": {key: ellipse[key] for key in (*COMMON_FIELDS, "fc8_s", "fcc_s", "fd0",
                            "fd4", "seg_tol", "fd8", *(key + "_s" for key in POINT_INDEX_FIELDS))},
        "creation_counters": fields["f140"], "state_fields": {key: fields[key] for key in (
            "f128", "f12c", "f130", "f134", "f568", "f56c", "f578")},
        "relations": fields["coinc"], "loop_manager_count": fields["f598"]["n"],
        "handle_manager_count": fields["f580"]["f40"]["n"],
        "seam_handle": {"owner": owner_record(link, handle), "class_slot": class_slot,
                        "wire": event_fields(handle_event), "fields": handle.FieldsValue},
    }


def geometry(members):
    points = {role: members["points"][index]["coordinates_m"] for role, index in members["point_bindings"].items()}
    center, major, minor, major_other, minor_other, seam = (points[key] for key in (*POINT_ROLES, "Seam"))
    u, v = difference(major, center), difference(minor, center)
    a, b = hypot(*u), hypot(*v)
    require(0 < b < a and isclose(dot(u, v), 0.0, rel_tol=0.0, abs_tol=1e-19)
            and near(difference(center, major_other), u) and near(difference(center, minor_other), v),
            "ellipse point ownership does not give signed orthogonal opposites")
    seam_vector = difference(seam, center)
    cosine, sine = dot(seam_vector, u) / a**2, dot(seam_vector, v) / b**2
    require(isclose(hypot(cosine, sine), 1.0, rel_tol=0.0, abs_tol=1e-13)
            and not near(seam, major), "sketch seam is missing or lies off the actual ellipse")
    return {"center_m": center, "radii_m": (a, b), "major_direction": tuple(x / a for x in u),
            "minor_direction": tuple(x / b for x in v), "sketch_seam_cos_sin": (cosine, sine),
            "sketch_seam_phase_degrees": degrees(atan2(sine, cosine))}


def compare_native(case, members, extrusion, names, frame, enums):
    support, profile, boss = names
    depth = extrusion.RequireDepth().DepthValue
    require(frame == ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
            and len(extrusion.ParentsValue) == 1 and not extrusion.IsReversed and extrusion.SecondValue is None,
            "ellipse profile did not retain its canonical Front blind ownership")
    require(depth.name == "D1" and depth.native_role == "driving",
            "linked extrusion lacks its actual D1 owner")
    for state in case["observations"]:
        topo, driver, definition = (state[name] for name in ("profile", "driver", "definition"))
        require(topo["support"] == support and topo["support_kind"] == enums["swSelDATUMPLANES"]
                and topo["contour_closed"] and topo["contour_members"] == 1 and not topo["relation_types"]
                and topo["frame"] == [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
                and topo["segment_id"][-1] == members["segment_fields"]["f0c"],
                "native COM profile does not agree with the typed full ellipse")
        for role in POINT_ROLES[:3]:
            row = members["points"][members["point_bindings"][role]]
            require((*row["coordinates_m"], 0.0) == tuple(topo["points_m"][role])
                    and row["persistent_words"][-1] == topo["point_ids"][role][-1],
                    f"typed {role} does not match its COM coordinate and creation identity")
        require(driver["name"].split("@")[:2] == [depth.name, boss]
                and driver["state"] == enums["swDimensionDriving"] and not driver["readonly"]
                and driver["value_m"] == definition["depth_m"] == depth.native_value
                and definition["type"] == "Extrusion" and definition["end"] == enums["swEndCondBlind"]
                and definition["start"] == 0 and set(definition["parents"]) == {profile, support}
                and definition["children"] == [profile]
                and not any(definition[key] for key in ("reverse", "two_directions", "draft", "thin")),
                "native COM D1 or actual owner path differs from the typed archive")
    rim = case["rim"]
    major = members["points"][members["point_bindings"]["Major"]]["coordinates_m"]
    require(rim["closed"] and rim["periodic"] and rim["success"] and rim["trim"] == rim["base"] == [0.0, 2*pi]
            and all(near(point[:2], major) for point in rim["seam_points_m"]),
            "independent cap trim does not lie at the major-axis station")


def read_owners(link, observed, case, enums):
    features = IndexFeatures(link)
    (boss,) = [node for node in features.values() if node.ClassValue.NameValue == "moExtrusion_c"]
    extrusion = ReadExtrude(link, boss, features)
    profile = extrusion.ProfileValue
    require(extrusion.ModeValue.value == "blind", "typed extrusion end is not blind")
    ref = RequireNative(profile.FieldsValue["pd_f78"], "moCompRefPlane_c")
    support = RequireNative(features[ref.FieldsValue["ff0"]["f00"]], "moRefPlane_c")
    frame_value = ReadPrismFrame(profile, link.ConfigValue.RootValue, features)
    frame = tuple(vector3(vector) for vector in (frame_value.origin, frame_value.x_axis,
                                                frame_value.y_axis, frame_value.z_axis))
    members = resolve_row(link, RequireNative(profile.FieldsValue["pd_f80"], "sgSketch"), observed)
    names = tuple(ReadNativeName(node) for node in (support, profile, boss))
    compare_native(case, members, extrusion, names, frame, enums)
    depth = extrusion.RequireDepth()
    return {
        "features": {"support": owner_record(link, support) | {"id": NativeNodeId(support), "name": names[0]},
                     "profile": owner_record(link, profile) | {"id": NativeNodeId(profile), "name": names[1]},
                     "boss": owner_record(link, boss) | {"id": NativeNodeId(boss), "name": names[2]},
                     "plane_reference": owner_record(link, ref), "frame_mm": frame},
        "depth": {"owner_path": "f818.f18/f850.ff0.f28.f58", "value_m": depth.DepthValue.native_value,
                  "persistent_dimension_id": depth.Dimension.FieldsValue["f50"], "name": depth.DepthValue.name,
                  "owners": [owner_record(link, item) for item in (extrusion.EndValue, depth.DisplayValue,
                                                                  depth.HandleValue, depth.Dimension, depth.Parameter)]},
        "sketch": members | geometry(members), "measured_cap_seam_xy_m": case["rim"]["seam_points_m"][0][:2],
        "com_observations": len(case["observations"]),
    }
